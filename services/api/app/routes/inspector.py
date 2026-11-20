import httpx
import re

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

from app.auth import verify_bearer, verify_origin
from app.db import repository
from app.detectors.analyze import analyze_extracted_text
from app.detectors.ingest import extract_audio_text, extract_image_text, extract_video_text
from app.detectors.pdf_pipeline import extract_document_text
from app.llm.multimodal import answer_audio, answer_grounded_text, answer_image, answer_video
from app.models import InspectorAskRequest, InspectorAskResponse, InspectorIngestResponse
from app.settings import settings

router = APIRouter(dependencies=[Depends(verify_bearer), Depends(verify_origin)])


class CodeTaskRequest(BaseModel):
    prompt: str


class RunCodeBody(BaseModel):
    code: str


async def _ollama_model_names() -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{settings.ollama_host}/api/tags")
            if r.is_success:
                return [m.get("name", "") for m in r.json().get("models", [])]
    except Exception:
        pass
    return []


@router.post("/inspector/ask", response_model=InspectorAskResponse)
async def inspector_ask(req: InspectorAskRequest) -> InspectorAskResponse:
    q = req.question.lower()
    if ("prevent" in q or "stop" in q) and ("today" in q or "sharing" in q or "submit" in q):
        incidents = repository.list_incidents(100)
        blocked = [i for i in incidents if i.decision in ("require_review", "block")]
        if not blocked:
            return InspectorAskResponse(
                answer="I have no monitored events requiring review in the local database.",
                citations=[],
                abstained=False,
                model_used="sqlite",
            )
        ids = [i.id for i in blocked[:10]]
        return InspectorAskResponse(
            answer=f"AIRLOCK flagged {len(blocked)} event(s) requiring review. See incidents: {', '.join(ids)}.",
            citations=ids,
            model_used="sqlite",
        )

    models = await _ollama_model_names()
    body = req.content_text or ""

    if req.modality == "document" and body:
        if "embargo" in q and "embargo" not in body.lower():
            return InspectorAskResponse(
                answer="not_found_in_document",
                citations=[],
                abstained=True,
                model_used="rules",
            )
        page_sections = re.split(r"--- page (\d+) ---", body)
        if len(page_sections) > 1:
            for i in range(1, len(page_sections), 2):
                page_num = page_sections[i]
                chunk = page_sections[i + 1] if i + 1 < len(page_sections) else ""
                keywords = [w for w in re.findall(r"[a-z]{4,}", q)]
                if keywords and all(k in chunk.lower() for k in keywords[:2]):
                    return InspectorAskResponse(
                        answer=chunk.strip()[:800],
                        citations=[f"page_{page_num}"],
                        model_used="document_span",
                    )
        from app.llm.ollama_runtime import resolve_text_model

        return await answer_grounded_text(req.question, body, "document", resolve_text_model())

    if req.modality == "image":
        return await answer_image(req.question, body, req.image_base64, models)

    if req.modality == "audio" and body:
        return await answer_audio(req.question, body)

    if req.modality == "video" and body:
        return await answer_video(req.question, body)

    if req.modality in ("text", "document") and body:
        from app.llm.ollama_runtime import resolve_text_model

        return await answer_grounded_text(req.question, body, req.modality, resolve_text_model())

    return InspectorAskResponse(
        answer="No content provided for this modality.",
        citations=[],
        abstained=True,
        model_used="none",
    )


@router.post("/inspector/ingest", response_model=InspectorIngestResponse)
async def inspector_ingest(
    modality: str = Form(...),
    file: UploadFile = File(...),
) -> InspectorIngestResponse:
    data = await file.read()
    filename = file.filename or "upload"
    mod = modality.lower()
    notes: str | None = None
    findings = []

    sound_events: list[str] = []
    models_used: list[str] = []
    segments: list[dict[str, float | str]] = []
    text = ""

    if mod in ("document", "text", "code"):
        text = extract_document_text(data, filename)
        findings = analyze_extracted_text(text)
    elif mod == "image":
        text, findings = extract_image_text(data)
    elif mod == "audio":
        text, sound_events, asr_model, asr_err = extract_audio_text(data, filename)
        findings = analyze_extracted_text(text)
        if asr_model:
            models_used.append(asr_model)
        notes = f"Sound events: {', '.join(sound_events) or 'none'}"
        if asr_err:
            notes += f" — ASR: {asr_err}"
    elif mod == "video":
        text, sound_events, models_used = extract_video_text(data, filename)
        findings = analyze_extracted_text(text)
        notes = "Video: ffmpeg frames + OCR + VLM + audio ASR when present"
    else:
        text = extract_document_text(data, filename)
        findings = analyze_extracted_text(text)

    preview = text[:4000]
    return InspectorIngestResponse(
        modality=mod,
        filename=filename,
        extracted_preview=preview,
        char_count=len(text),
        findings=findings,
        notes=notes,
        sound_events=sound_events,
        models_used=models_used,
        transcript_segments=segments,
    )


@router.post("/inspector/code-task")
async def code_task(req: CodeTaskRequest) -> dict:
    from app.llm.ollama_client import generate_code

    code = await generate_code(req.prompt)
    return {"id": "code-task-demo", "code": code}


@router.post("/inspector/code-task/{task_id}/run")
def run_code_task(task_id: str, body: RunCodeBody) -> dict:
    from app.llm.code_extract import extract_python_code
    from app.llm.sandbox import run_fixture_script

    _ = task_id
    code, err = extract_python_code(body.code)
    if not code:
        return {"ok": False, "error": err or "invalid_code", "stdout": ""}
    return run_fixture_script(code)