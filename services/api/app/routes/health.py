import httpx
from fastapi import APIRouter

from app.models import HealthResponse
from app.settings import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    ollama_ok = False
    models: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{settings.ollama_host}/api/tags")
            if r.is_success:
                ollama_ok = True
                data = r.json()
                models = [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        ollama_ok = False
    return HealthResponse(
        status="ok",
        ollama_reachable=ollama_ok,
        ollama_models=models,
        offline_ready=True,
    )