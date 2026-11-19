from app.models import Finding


def redact_text(content: str, findings: list[Finding], finding_ids: list[str]) -> str:
    selected = [f for f in findings if f.id in finding_ids]
    spans = []
    for f in selected:
        if f.anchor.kind == "text_span" and f.anchor.start is not None and f.anchor.end is not None:
            spans.append((f.anchor.start, f.anchor.end, f.category))
    spans.sort(key=lambda x: x[0], reverse=True)
    out = content
    counter: dict[str, int] = {}
    for start, end, cat in spans:
        counter[cat] = counter.get(cat, 0) + 1
        placeholder = f"[REDACTED_{cat.upper()}_{counter[cat]}]"
        out = out[:start] + placeholder + out[end:]
    return out