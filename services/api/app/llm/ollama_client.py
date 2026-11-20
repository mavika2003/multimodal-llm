import base64
import httpx

from app.llm.code_extract import extract_python_code
from app.llm.ollama_runtime import ollama_semaphore, resolve_text_model
from app.settings import settings


async def ask_ollama_text(prompt: str, model: str | None = None) -> str:
    use_model = model or resolve_text_model()
    async with ollama_semaphore():
        try:
            async with httpx.AsyncClient(timeout=settings.scan_timeout_seconds) as client:
                r = await client.post(
                    f"{settings.ollama_host}/api/generate",
                    json={"model": use_model, "prompt": prompt, "stream": False},
                )
                if r.is_success:
                    return (r.json().get("response") or "").strip()
        except Exception:
            pass
    return "not_found"


def describe_image_sync(
    question: str,
    image_bytes: bytes,
    model: str | None = None,
    timeout: float | None = None,
) -> str:
    use_model = model or settings.ollama_vlm_model
    b64 = base64.b64encode(image_bytes).decode()
    prompt = f"{question}\nAnswer only from the image. If unsure, say not_found_in_image."
    http_timeout = timeout if timeout is not None else settings.scan_timeout_seconds
    try:
        with httpx.Client(timeout=http_timeout) as client:
            r = client.post(
                f"{settings.ollama_host}/api/chat",
                json={
                    "model": use_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                            "images": [b64],
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


async def generate_code(prompt: str) -> str:
    model = settings.ollama_coder_model
    default = '''import json
from pathlib import Path
data = json.loads(Path("incidents.json").read_text())
by_mod = {}
for row in data:
    m = row.get("modality", "unknown")
    by_mod[m] = by_mod.get(m, 0) + 1
print(json.dumps(by_mod, indent=2))
'''
    async with ollama_semaphore():
        try:
            async with httpx.AsyncClient(timeout=settings.scan_timeout_seconds) as client:
                r = await client.post(
                    f"{settings.ollama_host}/api/generate",
                    json={
                        "model": model,
                        "prompt": (
                            "Write minimal Python 3 script only. No markdown fences. "
                            f"No explanation.\n{prompt}"
                        ),
                        "stream": False,
                    },
                )
                if r.is_success:
                    text = (r.json().get("response") or "").strip()
                    if text:
                        normalized, err = extract_python_code(text)
                        if normalized:
                            return normalized
                        if err:
                            return default
                        return text
        except Exception:
            pass
    return default