"""Video: timestamped frames, OCR, optional VLM, audio transcript."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.audio.acoustic_events import classify_acoustic_events, labels_from_events
from app.detectors.ocr import scan_image_bytes
from app.detectors.secrets import scan_text_secrets
from app.llm.ollama_client import describe_image_sync
from app.models import Finding, SourceAnchor
from app.llm.whisper_local import transcribe_audio_file
from app.scan.diagnostics import ScanDiagnostics
from app.settings import settings

logger = logging.getLogger("airlock.scan")

ScanProfile = Literal["firewall", "inspector"]


@dataclass
class VideoExtractResult:
    text: str
    frame_times: list[float]
    vlm_summaries: list[tuple[float, str]]
    sound_events: list[str]
    transcript: str
    models_used: list[str]
    stages_ms: dict[str, float] | None = None
    notes: list[str] | None = None
    frame_findings: list[Finding] | None = None


def _probe_duration(video_path: Path) -> float:
    try:
        out = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return float(out.stdout.strip() or "10")
    except Exception:
        return 10.0


def _suffix_for_name(filename: str) -> str:
    low = filename.lower()
    for ext in (".mp4", ".webm", ".mov", ".mkv", ".m4v", ".avi"):
        if low.endswith(ext):
            return ext
    return ".mp4"


def extract_video_enhanced(
    data: bytes,
    filename: str,
    *,
    profile: ScanProfile = "inspector",
    diag: ScanDiagnostics | None = None,
) -> VideoExtractResult:
    if not shutil.which("ffmpeg"):
        return VideoExtractResult(
            f"[Video {filename}: ffmpeg required]",
            [],
            [],
            [],
            "",
            [],
            None,
            None,
            [],
        )

    wall_deadline = time.monotonic() + (
        settings.video_scan_wall_deadline_sec
        if profile == "firewall"
        else settings.video_scan_wall_deadline_sec * 2
    )
    max_duration = (
        settings.video_firewall_max_duration_sec
        if profile == "firewall"
        else settings.video_max_duration_sec
    )
    max_vlm = (
        settings.video_firewall_max_vlm_frames
        if profile == "firewall"
        else settings.video_max_vlm_frames
    )
    max_ocr = (
        settings.video_firewall_max_ocr_frames
        if profile == "firewall"
        else max(max_vlm * 3, settings.video_max_vlm_frames)
    )
    max_audio = (
        settings.video_firewall_max_audio_sec
        if profile == "firewall"
        else settings.video_max_duration_sec
    )
    frame_interval = settings.video_frame_interval_sec

    models: list[str] = []
    stages: dict[str, float] = {}
    notes: list[str] = []

    def over_deadline() -> bool:
        return time.monotonic() > wall_deadline

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        ext = _suffix_for_name(filename)
        src = td_path / f"in{ext}"
        src.write_bytes(data)

        t0 = time.perf_counter()
        duration = min(_probe_duration(src), max_duration)
        stages["probe_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        times: list[float] = []
        t = 0.0
        while t <= duration and len(times) < max_ocr:
            times.append(t)
            t += frame_interval

        chunks: list[str] = []
        vlm_summaries: list[tuple[float, str]] = []
        frame_ocr: list[tuple[float, str, bytes]] = []
        frame_findings: list[Finding] = []

        for sec in times:
            if over_deadline():
                notes.append("scan_deadline_reached_before_all_frames")
                break
            frame = td_path / f"frame_{sec:.1f}.jpg"
            try:
                t_fr = time.perf_counter()
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        str(src),
                        "-ss",
                        str(sec),
                        "-vframes",
                        "1",
                        "-vf",
                        "scale='min(1920,iw*2)':-2",
                        "-q:v",
                        "2",
                        str(frame),
                    ],
                    check=True,
                    capture_output=True,
                    timeout=60,
                )
                stages[f"ffmpeg_frame_{sec}s_ms"] = round((time.perf_counter() - t_fr) * 1000, 1)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                continue
            if not frame.exists():
                continue
            img_data = frame.read_bytes()
            ocr_text, ocr_findings = scan_image_bytes(img_data)
            for f in ocr_findings:
                if f.anchor.kind == "image_box":
                    f.anchor = SourceAnchor(
                        kind=f.anchor.kind,
                        page_or_frame=int(sec),
                        bbox_xyxy=f.anchor.bbox_xyxy,
                    )
                else:
                    f.anchor = SourceAnchor(
                        kind=f.anchor.kind,
                        start=f.anchor.start,
                        end=f.anchor.end,
                        page_or_frame=int(sec),
                    )
            frame_findings.extend(ocr_findings)
            chunks.append(f"[t={sec}s] OCR: {ocr_text.strip() or '(none)'}")
            frame_ocr.append((sec, ocr_text, img_data))

        # VLM: firewall runs on at most 2 frames (longest OCR text first)
        vlm_targets = frame_ocr
        if profile == "firewall" and len(vlm_targets) > settings.video_firewall_max_vlm_frames:
            ranked = sorted(vlm_targets, key=lambda x: len(x[1].strip()), reverse=True)
            vlm_targets = ranked[: settings.video_firewall_max_vlm_frames]
            if len(vlm_targets) < settings.video_firewall_max_vlm_frames:
                seen_secs = {x[0] for x in vlm_targets}
                for row in frame_ocr:
                    if row[0] in seen_secs:
                        continue
                    vlm_targets.append(row)
                    seen_secs.add(row[0])
                    if len(vlm_targets) >= settings.video_firewall_max_vlm_frames:
                        break
        elif not vlm_targets and times:
            notes.append("no_video_frames_extracted")

        for sec, ocr_text, img_data in vlm_targets:
            if over_deadline():
                notes.append("scan_deadline_reached_before_vlm_complete")
                break
            t_vlm = time.perf_counter()
            vlm = describe_image_sync(
                (
                    "Transcribe every line of visible text exactly (especially shell/terminal "
                    "commands and export statements). Then list any credentials, tokens, or secrets."
                ),
                img_data,
                timeout=settings.video_firewall_vlm_timeout_sec
                if profile == "firewall"
                else settings.scan_timeout_seconds,
            )
            stages[f"vlm_{sec}s_ms"] = round((time.perf_counter() - t_vlm) * 1000, 1)
            if vlm:
                vlm_summaries.append((sec, vlm))
                chunks.append(f"[t={sec}s] VLM: {vlm}")
                models.append(settings.ollama_vlm_model)
                for f in scan_text_secrets(vlm, detector_prefix="vlm_ocr_rules"):
                    f.anchor = SourceAnchor(
                        kind=f.anchor.kind,
                        start=f.anchor.start,
                        end=f.anchor.end,
                        page_or_frame=int(sec),
                    )
                    frame_findings.append(f)

        wav = td_path / "audio.wav"
        transcript = ""
        sound_events: list[str] = []
        if not over_deadline():
            try:
                t_au = time.perf_counter()
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        str(src),
                        "-t",
                        str(max_audio),
                        "-vn",
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
                stages["ffmpeg_audio_ms"] = round((time.perf_counter() - t_au) * 1000, 1)
                if wav.exists():
                    t_wh = time.perf_counter()
                    tr = transcribe_audio_file(wav)
                    stages["whisper_ms"] = round((time.perf_counter() - t_wh) * 1000, 1)
                    if tr.transcript:
                        transcript = tr.transcript
                        chunks.append(f"[audio_transcript] {transcript}")
                        models.append(tr.model_used)
                    elif tr.error:
                        notes.append(f"asr_error:{tr.error}")
                    events = classify_acoustic_events(str(wav))
                    sound_events = labels_from_events(events)
                    if sound_events:
                        chunks.append(f"[acoustic_events] {', '.join(sound_events)}")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                notes.append(f"audio_extract_failed:{type(e).__name__}")

        if notes:
            chunks.append("[scan_meta] " + "; ".join(notes))

        body = (
            f"Video analysis ({profile}) for {filename} (duration~{duration:.1f}s):\n"
            + "\n".join(chunks)
        )
        if diag:
            diag.stages_ms.update(stages)
            for n in notes:
                diag.note(n)

        return VideoExtractResult(
            body,
            times,
            vlm_summaries,
            sound_events,
            transcript,
            models,
            stages,
            notes,
            frame_findings,
        )