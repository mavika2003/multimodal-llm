import httpx

from app.settings import settings


async def ask_ollama_text(prompt: str) -> str:
    if not settings.ollama_vlm_model and not settings.ollama_coder_model:
        return "Local model not configured; using rule-based abstention."
    model = settings.ollama_coder_model or "llama3.2"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{settings.ollama_host}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            if r.is_success:
                return (r.json().get("response") or "").strip()
    except Exception:
        pass
    return "not_found"


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
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{settings.ollama_host}/api/generate",
                json={
                    "model": model,
                    "prompt": f"Write minimal Python 3 script only, no markdown:\n{prompt}",
                    "stream": False,
                },
            )
            if r.is_success:
                text = (r.json().get("response") or "").strip()
                if text:
                    return text
    except Exception:
        pass
    return default