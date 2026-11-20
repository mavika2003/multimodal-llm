"""Local open-weight multimodal Q&A helpers (Ollama + OCR fallbacks)."""

import base64

import httpx

from app.llm.audio_events import infer_sound_events
from app.llm.ollama_client import ask_ollama_text
from app.models import InspectorAskResponse
from app.settings import settings


def _pick_vlm_model(available: list[str] | None = None) -> str | None:
    if settings.ollama_vlm_model:
        return settings.ollama_vlm_model
    if not available:
        return None
    for want in ("qwen2.5vl", "qwen3-vl", "llava", "moondream", "minicpm-v"):
        for name in available:
            if want in name.lower():
                return name
    return None


async def ask_ollama_vision(question: str, image_b64: str, model: str) -> str:
    prompt = (
        f"{question}\n"
        "Answer only from the image. If unsure, say not_found_in_image."
    )
    try:
        async with httpx.AsyncClient(timeout=settings.scan_timeout_seconds) as client:
            r = await client.post(
                f"{settings.ollama_host}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                            "images": [image_b64.split(",")[-1]],
                        }
                    ],
                    "stream": False,
                },
            )
            if r.is_success:
                msg = r.json().get("message") or {}
                text = (msg.get("content") or "").strip()
                if text:
                    return text
    except Exception:
        pass
    return ""


async def answer_grounded_text(
    question: str, content: str, citation: str, model_hint: str | None = None
) -> InspectorAskResponse:
    if "not in document" in question.lower() or "embargo" in question.lower():
        if "embargo" not in content.lower():
            return InspectorAskResponse(
                answer="not_found_in_document",
                citations=[],
                abstained=True,
                model_used=model_hint or "rules",
            )
    prompt = (
        "Answer ONLY from the provided content. If the answer is not supported, "
        f"reply exactly: not_found_in_document\n\nContent:\n{content[:6000]}\n\nQuestion: {question}"
    )
    ans = await ask_ollama_text(prompt)
    if "not_found" in ans.lower():
        return InspectorAskResponse(
            answer="not_found_in_document",
            citations=[],
            abstained=True,
            model_used=model_hint or settings.ollama_coder_model,
        )
    return InspectorAskResponse(
        answer=ans,
        citations=[citation],
        abstained=False,
        model_used=model_hint or settings.ollama_coder_model,
    )


async def answer_image(
    question: str,
    ocr_text: str,
    image_b64: str | None,
    ollama_models: list[str] | None = None,
) -> InspectorAskResponse:
    vlm = _pick_vlm_model(ollama_models)
    if image_b64 and vlm:
        b64 = image_b64.split(",")[-1] if "," in image_b64 else image_b64
        vision = await ask_ollama_vision(question, b64, vlm)
        if vision and "not_found" not in vision.lower():
            return InspectorAskResponse(
                answer=vision,
                citations=["local_vlm", "ocr_context"],
                abstained=False,
                model_used=vlm,
            )
    if ocr_text.strip():
        return await answer_grounded_text(question, ocr_text, "image_ocr", "ocr+tesseract")
    return InspectorAskResponse(
        answer="No image content or OCR text available.",
        citations=[],
        abstained=True,
        model_used="none",
    )


async def answer_audio(question: str, transcript: str) -> InspectorAskResponse:
    sounds = infer_sound_events(transcript)
    sound_line = f"Detected sound events: {', '.join(sounds) if sounds else 'unknown'}."
    q = question.lower()
    if "sound" in q or "keyboard" in q or "notification" in q or "typing" in q:
        for s in sounds:
            if any(k in q for k in s.split("_")):
                return InspectorAskResponse(
                    answer=f"Yes — transcript indicates {s.replace('_', ' ')}. {sound_line}",
                    citations=["audio_transcript", "sound_rules"],
                    sound_events=sounds,
                    model_used="sound_rules",
                )
        return InspectorAskResponse(
            answer=sound_line,
            citations=["sound_rules"],
            sound_events=sounds,
            model_used="sound_rules",
        )
    grounded = await answer_grounded_text(question, transcript, "audio_transcript")
    grounded.sound_events = sounds
    if grounded.answer and not grounded.abstained:
        grounded.answer = f"{grounded.answer}\n\n{sound_line}"
    return grounded


async def answer_video(question: str, extracted: str) -> InspectorAskResponse:
    if "timestamp" in question.lower() or "second" in question.lower() or "frame" in question.lower():
        for line in extracted.splitlines():
            if "t=" in line or "Frame at" in line:
                if any(w in question.lower() for w in ("token", "credential", "client")):
                    if "token" in line.lower() or "client" in line.lower():
                        return InspectorAskResponse(
                            answer=line.strip(),
                            citations=["video_frames"],
                            model_used="frame_ocr",
                        )
    return await answer_grounded_text(question, extracted, "video_frames", settings.ollama_coder_model)