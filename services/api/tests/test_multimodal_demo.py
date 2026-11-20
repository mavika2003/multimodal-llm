from pathlib import Path

from app.llm.audio_events import infer_sound_events
from app.llm.multimodal import answer_grounded_text
import pytest


ROOT = Path(__file__).resolve().parents[3]
DOC = (ROOT / "fixtures" / "multimodal_demo" / "demo_document.txt").read_text()
AUDIO = (ROOT / "fixtures" / "multimodal_demo" / "demo_audio_transcript.txt").read_text()


def test_audio_sound_events():
    events = infer_sound_events(AUDIO)
    assert "speech" in events
    assert "keyboard_typing" in events


@pytest.mark.asyncio
async def test_document_abstains_embargo():
    res = await answer_grounded_text(
        "What is the embargo date?",
        DOC,
        "document",
    )
    assert res.abstained or "not_found" in res.answer.lower()


def test_hackathon_fixtures_exist():
    assert (ROOT / "fixtures" / "multimodal_demo" / "demo_document.txt").is_file()