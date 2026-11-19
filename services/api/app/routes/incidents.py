from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import verify_bearer, verify_origin
from app.db import repository
from app.models import AnalyticsSummary, IncidentDetail, IncidentSummary

router = APIRouter(dependencies=[Depends(verify_bearer), Depends(verify_origin)])


@router.get("/incidents", response_model=list[IncidentSummary])
def list_incidents(limit: int = 50) -> list[IncidentSummary]:
    return repository.list_incidents(limit=limit)


@router.get("/incidents/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: str) -> IncidentDetail:
    detail = repository.get_incident(incident_id)
    if not detail:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return detail


class TriagePatch(BaseModel):
    review_status: str
    resolution: str | None = None


@router.patch("/incidents/{incident_id}/triage")
def triage(incident_id: str, body: TriagePatch) -> dict:
    ok = repository.update_triage(incident_id, body.review_status, body.resolution)
    if not ok:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return {"ok": True, "incident_id": incident_id}


@router.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics() -> AnalyticsSummary:
    return AnalyticsSummary(**repository.analytics_summary())