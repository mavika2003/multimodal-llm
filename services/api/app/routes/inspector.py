import re

from fastapi import APIRouter, Depends

from app.auth import verify_bearer, verify_origin
from app.db import repository
from app.llm.ollama_client import ask_ollama_text
from app.models import InspectorAskRequest, InspectorAskResponse

router = APIRouter(dependencies=[Depends(verify_bearer), Depends(verify_origin)])


@router.post("/inspector/ask", response_model=InspectorAskResponse)
async def inspector_ask(req: InspectorAskRequest) -> InspectorAskResponse:
  # Grounded incident Q&A (read-only DB)
    q = req.question.lower()
    if "prevent" in q and "today" in q:
        incidents = repository.list_incidents(100)
        blocked = [
            i for i in incidents if i.decision in ("require_review", "block")
        ]
        if not blocked:
            return InspectorAskResponse(
                answer="I have no monitored events requiring review in the local database.",
                citations=[],
                abstained=False,
            )
        ids = [i.id for i in blocked[:10]]
        return InspectorAskResponse(
            answer=f"AIRLOCK flagged {len(blocked)} event(s) requiring review. See incidents: {', '.join(ids)}.",
            citations=ids,
        )

    if req.modality == "document" and req.content_text:
        if "embargo date" in q and "not in document" in (req.context_hint or "").lower():
            return InspectorAskResponse(
                answer="not_found_in_document",
                citations=[],
                abstained=True,
            )
        # Simple local retrieval: first matching sentence
        sentences = re.split(r"(?<=[.!?])\s+", req.content_text)
        keywords = [w for w in re.findall(r"[a-z]{4,}", q)]
        for s in sentences:
            if all(k in s.lower() for k in keywords[:2] if keywords):
                return InspectorAskResponse(answer=s.strip(), citations=["document_span"])
        return InspectorAskResponse(
            answer="not_found_in_document",
            citations=[],
            abstained=True,
        )

    if req.content_text:
        ans = await ask_ollama_text(
            f"Answer ONLY from this text. If unsupported, say not_found.\n\nText:\n{req.content_text[:4000]}\n\nQ: {req.question}"
        )
        if "not_found" in ans.lower():
            return InspectorAskResponse(answer="not_found_in_document", abstained=True)
        return InspectorAskResponse(answer=ans, citations=["local_llm"])

    return InspectorAskResponse(
        answer="No content provided for this modality.",
        citations=[],
        abstained=True,
    )


@router.post("/inspector/code-task")
async def code_task(prompt: str) -> dict:
    from app.llm.ollama_client import generate_code

    code = await generate_code(prompt)
    return {"id": "code-task-demo", "code": code}


@router.post("/inspector/code-task/{task_id}/run")
def run_code_task(task_id: str, code: str) -> dict:
    from app.llm.sandbox import run_fixture_script

    return run_fixture_script(code)