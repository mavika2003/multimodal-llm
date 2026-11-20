from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

FIXTURES = Path(__file__).resolve().parents[4] / "fixtures" / "multimodal_demo"

DEMO_MANIFEST = [
    {
        "id": "document",
        "modality": "document",
        "file": "demo_document.txt",
        "sample_question": "When does Project Phoenix launch?",
        "abstention_question": "What is the embargo date for press releases?",
    },
    {
        "id": "document_missing",
        "modality": "document",
        "file": "demo_document.txt",
        "sample_question": "What is the embargo date?",
        "context_hint": "not in document",
    },
    {
        "id": "image",
        "modality": "image",
        "file": "screenshot_labels.png",
        "sample_question": "What credential-like text appears in this screenshot?",
    },
    {
        "id": "audio",
        "modality": "audio",
        "file": "demo_audio_transcript.txt",
        "sample_question": "Was keyboard typing present?",
    },
    {
        "id": "video",
        "modality": "video",
        "file": "demo_video_transcript.txt",
        "sample_question": "At what timestamp is a client token visible?",
    },
]


@router.get("/demo/hackathon-manifest")
def hackathon_manifest() -> dict:
    return {"items": DEMO_MANIFEST, "fixture_root": str(FIXTURES)}


@router.get("/demo/fixtures/{filename}")
def demo_fixture_file(filename: str):
    safe = Path(filename).name
    path = FIXTURES / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="FIXTURE_NOT_FOUND")
    return FileResponse(path)