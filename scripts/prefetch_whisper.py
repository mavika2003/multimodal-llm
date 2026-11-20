#!/usr/bin/env python3
"""Pre-download faster-whisper weights (run once while online)."""

import sys
from pathlib import Path

API = Path(__file__).resolve().parents[1] / "services" / "api"
sys.path.insert(0, str(API))

from app.settings import settings  # noqa: E402

from faster_whisper import WhisperModel  # noqa: E402

WhisperModel(
    settings.whisper_model_size,
    device=settings.whisper_device,
    compute_type=settings.whisper_compute_type,
    download_root=str(settings.whisper_cache_dir),
)
print(f"Whisper {settings.whisper_model_size} cached at {settings.whisper_cache_dir}")