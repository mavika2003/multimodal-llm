"""Lightweight sound-event labels from transcript text (hackathon demo)."""

import re

SOUND_RULES: list[tuple[str, list[str]]] = [
    ("speech", [r"\bspeaker\b", r"\bsaid\b", r"\bremember\b", r"\bdon't\b", r"\bshare\b"]),
    ("keyboard_typing", [r"keyboard", r"typing"]),
    ("notification", [r"notification", r"chime", r"beep", r"alert"]),
    ("silence", [r"\(silence\)", r"\[silence\]"]),
]


def infer_sound_events(transcript: str) -> list[str]:
    t = transcript.lower()
    found: list[str] = []
    for label, patterns in SOUND_RULES:
        if any(re.search(p, t) for p in patterns):
            found.append(label)
    if not found and len(transcript.strip()) > 40:
        found.append("speech")
    return found