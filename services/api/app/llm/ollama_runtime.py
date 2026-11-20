"""Shared Ollama model resolution and concurrency."""

import asyncio
import re

from app.settings import settings

_ollama_sem = asyncio.Semaphore(max(1, settings.ollama_max_concurrent_requests))


def ollama_semaphore() -> asyncio.Semaphore:
    return _ollama_sem


def resolve_vlm_model(available: list[str] | None) -> str | None:
    if settings.ollama_vlm_model:
        want = settings.ollama_vlm_model
        if available:
            for name in available:
                if name == want or name.startswith(want.split(":")[0]):
                    return name
        return want
    if not available:
        return None
    priority = (
        r"qwen3\.5",
        r"qwen2\.5vl",
        r"qwen3-vl",
        r"llava",
        r"moondream",
        r"minicpm-v",
    )
    for pat in priority:
        for name in available:
            if re.search(pat, name, re.IGNORECASE):
                return name
    return None


def resolve_text_model() -> str:
    return settings.ollama_text_model or settings.ollama_coder_model or "qwen2.5-coder:3b"