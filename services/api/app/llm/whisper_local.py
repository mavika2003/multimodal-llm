"""Local speech transcription via faster-whisper (offline cache)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.settings import settings

_whisper_model = None


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptResult:
    transcript: str
    segments: list[TranscriptSegment]
    model_used: str
    error: str | None = None


def _get_model():
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError("faster_whisper not installed in API venv") from e
    _whisper_model = WhisperModel(
        settings.whisper_model_size,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
        download_root=str(settings.whisper_cache_dir),
        local_files_only=False,
    )
    return _whisper_model


def _load_audio_float32(wav_path: Path):
    """Load WAV via soundfile; avoids PyAV open(metadata_errors=...) breakage on some builds."""
    import numpy as np

    try:
        import soundfile as sf
    except ImportError as e:
        raise RuntimeError("soundfile not installed") from e
    audio, sr = sf.read(str(wav_path), dtype="float32", always_2d=False)
    if getattr(audio, "ndim", 1) > 1:
        audio = np.mean(audio, axis=1)
    if sr != 16000:
        # ffmpeg normalize step should already be 16 kHz; resample if not.
        try:
            import librosa

            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
        except Exception:
            pass
    return np.asarray(audio, dtype=np.float32)


def transcribe_audio_file(wav_path: Path) -> TranscriptResult:
    model_name = f"faster-whisper-{settings.whisper_model_size}"
    try:
        model = _get_model()
    except RuntimeError as e:
        return TranscriptResult("", [], model_name, error=str(e))

    try:
        audio_input = _load_audio_float32(wav_path)
        segments_iter, info = model.transcribe(
            audio_input,
            vad_filter=True,
            beam_size=1,
        )
        segments: list[TranscriptSegment] = []
        parts: list[str] = []
        for seg in segments_iter:
            text = (seg.text or "").strip()
            if not text:
                continue
            segments.append(TranscriptSegment(seg.start, seg.end, text))
            parts.append(text)
        transcript = " ".join(parts).strip()
        if not transcript and info.duration < 0.5:
            return TranscriptResult(
                "",
                [],
                model_name,
                error="silent_or_too_short",
            )
        return TranscriptResult(transcript, segments, model_name)
    except Exception as e:
        return TranscriptResult("", [], model_name, error=str(e))