"""Audio-based sound event heuristics on waveforms (not transcript keywords)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    import librosa
except ImportError:
    librosa = None

try:
    import soundfile as sf
except ImportError:
    sf = None


@dataclass
class AcousticEvent:
    label: str
    start_sec: float
    end_sec: float
    confidence_label: str
    method: str = "acoustic_analysis"


def classify_acoustic_events(wav_path: str, duration_hint: float | None = None) -> list[AcousticEvent]:
    if librosa is None or sf is None:
        return []
    try:
        y, sr = librosa.load(wav_path, sr=16000, mono=True)
    except Exception:
        return []

    try:
        return _classify_waveform(y, sr, duration_hint)
    except Exception:
        return []


def _classify_waveform(y: np.ndarray, sr: int, duration_hint: float | None) -> list[AcousticEvent]:
    if len(y) < sr * 0.1:
        return [
            AcousticEvent("silence", 0.0, max(0.1, duration_hint or 0.1), "high"),
        ]

    events: list[AcousticEvent] = []
    rms = librosa.feature.rms(y=y)[0]
    if float(np.mean(rms)) < 0.01:
        events.append(AcousticEvent("silence", 0.0, len(y) / sr, "high"))
        return events

    n_fft = 2048
    S = np.abs(librosa.stft(y, n_fft=n_fft))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    speech_band = (freqs >= 300) & (freqs <= 3400)
    speech_energy = S[speech_band, :].mean(axis=0)
    if float(np.mean(speech_energy)) > np.percentile(speech_energy, 60):
        events.append(AcousticEvent("speech", 0.0, len(y) / sr, "medium"))

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units="time")
    hf_idx = freqs >= 2000
    hf_mean = S[hf_idx, :].mean()
    if len(onsets) >= 8 and hf_mean > 0.02:
        events.append(
            AcousticEvent(
                "keyboard_typing",
                float(onsets[0]),
                float(onsets[-1]) if len(onsets) else len(y) / sr,
                "medium",
            )
        )

    # Notification / alert: narrow-band tonal peak
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    if float(chroma.max()) > 0.6 and len(onsets) <= 3:
        events.append(AcousticEvent("notification", 0.0, min(2.0, len(y) / sr), "low"))

    # Background music: strong harmonic content over sustained period
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    if tempo and float(np.std(rms)) < 0.02 and float(np.mean(rms)) > 0.03:
        events.append(AcousticEvent("background_music", 0.0, len(y) / sr, "low"))

    if not events:
        events.append(AcousticEvent("speech", 0.0, len(y) / sr, "low"))

    return events


def labels_from_events(events: list[AcousticEvent]) -> list[str]:
    return [e.label for e in events]