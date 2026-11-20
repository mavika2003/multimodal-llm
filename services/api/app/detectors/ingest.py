import shutil
import subprocess
import tempfile
from pathlib import Path

from app.audio.acoustic_events import classify_acoustic_events, labels_from_events
from app.detectors.analyze import analyze_extracted_text
from app.detectors.ocr import scan_image_bytes
from app.detectors.pdf_pipeline import extract_document_text
from app.detectors.video_pipeline import extract_video_enhanced
from app.llm.audio_events import infer_sound_events
from app.llm.whisper_local import transcribe_audio_file

def extract_image_text(data: bytes) -> tuple[str, list]:
    text, findings = scan_image_bytes(data)
    return text, findings


def extract_audio_text(data: bytes, filename: str) -> tuple[str, list[str], str | None, str | None]:
    """Returns text, sound_event_labels, model_used, error."""
    lower = filename.lower()
    if lower.endswith((".txt", ".srt", ".vtt", ".md")):
        text = data.decode("utf-8", errors="replace")
        sounds = infer_sound_events(text) + labels_from_events([])
        return text, sounds, "transcript_file", None

    if not shutil.which("ffmpeg"):
        return (
            f"[Audio {filename}: ffmpeg required for raw audio]",
            [],
            None,
            "ffmpeg_missing",
        )

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        src = td_path / "in"
        wav = td_path / "norm.wav"
        src.write_bytes(data)
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(src),
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    str(wav),
                ],
                check=True,
                capture_output=True,
                timeout=120,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            return (
                f"[Could not decode audio {filename}]",
                [],
                None,
                str(e),
            )

        acoustic = classify_acoustic_events(str(wav))
        acoustic_labels = labels_from_events(acoustic)
        tr = transcribe_audio_file(wav)
        if tr.error and not tr.transcript:
            return (
                f"[Transcription failed: {tr.error}]",
                acoustic_labels,
                tr.model_used,
                tr.error,
            )
        text = tr.transcript
        if tr.segments:
            lines = [f"[{s.start:.1f}-{s.end:.1f}] {s.text}" for s in tr.segments]
            text = "\n".join(lines)
        rule_sounds = infer_sound_events(text)
        merged = list(dict.fromkeys(acoustic_labels + rule_sounds))
        return text, merged, tr.model_used, tr.error


def extract_video_text(
    data: bytes,
    filename: str,
    *,
    profile: str = "inspector",
) -> tuple[str, list[str], list[str]]:
    from app.detectors.video_pipeline import extract_video_enhanced

    res = extract_video_enhanced(data, filename, profile=profile)  # type: ignore[arg-type]
    return res.text, res.sound_events, res.models_used


def extract_video_text_firewall(
    data: bytes,
    filename: str,
    diag=None,
) -> tuple[str, list[str], list[str], list]:
    from app.detectors.video_pipeline import extract_video_enhanced

    res = extract_video_enhanced(data, filename, profile="firewall", diag=diag)
    return res.text, res.sound_events, res.models_used, res.frame_findings or []