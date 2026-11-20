from pathlib import Path

import numpy as np
import soundfile as sf

from app.audio.acoustic_events import classify_acoustic_events

ROOT = Path(__file__).resolve().parents[3]


def test_classify_demo_speech_wav():
    wav = ROOT / "fixtures" / "multimodal_demo" / "demo_speech.wav"
    if not wav.is_file():
        return
    events = classify_acoustic_events(str(wav))
    assert isinstance(events, list)


def test_classify_synthetic_noise(tmp_path):
    sr = 16000
    t = np.linspace(0, 1.0, sr)
    y = (0.1 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    path = tmp_path / "tone.wav"
    sf.write(path, y, sr)
    events = classify_acoustic_events(str(path))
    assert isinstance(events, list)