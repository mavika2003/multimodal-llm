# Hackathon demo fixtures (synthetic only)

Load these from **Dashboard → Inspector → Hackathon kit** or upload manually.

| File | Modality | Sample question |
|------|----------|-----------------|
| `demo_document.txt` | Text/document | "When does Project Phoenix launch?" |
| `demo_document.txt` | Abstention | "What is the embargo date?" → not in document |
| `screenshot_labels.png` | Image | "What credential-like text is visible?" |
| `demo_audio_transcript.txt` | Audio | "Was keyboard typing present?" |
| `demo_video_transcript.txt` | Video | "When does the terminal show a token?" |
| Code tab | Code | "Count incidents by modality from fixtures JSON" |

Generate or refresh image: `make demo-fixtures`