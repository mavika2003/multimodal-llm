from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Decision(str, Enum):
    allow = "allow"
    warn = "warn"
    require_review = "require_review"
    block = "block"
    unknown = "unknown"


class AnchorKind(str, Enum):
    text_span = "text_span"
    image_box = "image_box"


class SourceAnchor(BaseModel):
    kind: AnchorKind | str
    start: int | None = None
    end: int | None = None
    page_or_frame: int | None = None
    bbox_xyxy: list[int] | None = None


class Finding(BaseModel):
    id: str
    category: str
    severity: Literal["low", "medium", "high", "critical", "unknown"]
    detector: str
    confidence_label: str | None = None
    anchor: SourceAnchor
    excerpt_redacted: str
    explanation_redacted: str
    policy_rule_id: str | None = None


class TextScanRequest(BaseModel):
    action_id: str
    source: str = "local-demo-chat"
    destination_origin: str = "http://127.0.0.1:5173"
    modality: Literal["text", "code"] = "text"
    content: str
    payload_sha256: str | None = None


class ScanResponse(BaseModel):
    scan_id: str
    action_id: str
    state: Literal["decision_ready", "scanning", "failed"] = "decision_ready"
    decision: Decision
    findings: list[Finding] = Field(default_factory=list)
    transmission_status: Literal[
        "not_sent_confirmed", "sent_confirmed", "unknown"
    ] = "not_sent_confirmed"


class RedactRequest(BaseModel):
    action_id: str
    modality: Literal["text", "code", "image"]
    content_text: str | None = None
    finding_ids: list[str]
    findings: list[Finding]
    image_base64: str | None = None


class RedactResponse(BaseModel):
    sanitized_text: str | None = None
    sanitized_image_base64: str | None = None
    finding_ids: list[str]


class DecisionRecord(BaseModel):
    action_id: str
    choice: Literal["cancel", "override", "send_sanitized", "allow"]
    note: str | None = None


class IncidentSummary(BaseModel):
    id: str
    action_id: str
    observed_at: str
    modality: str
    severity: str
    decision: str
    workflow_state: str
    outcome: str
    transmission_status: str
    review_status: str
    title: str
    summary_redacted: str | None = None


class IncidentDetail(IncidentSummary):
    findings: list[Finding] = Field(default_factory=list)
    event_steps: list[dict[str, Any]] = Field(default_factory=list)


class AnalyticsSummary(BaseModel):
    actions_scanned: int
    review_required: int
    prevented: int
    by_modality: dict[str, int]


class InspectorAskRequest(BaseModel):
    modality: Literal["text", "document", "image", "audio", "video"]
    question: str
    content_text: str | None = None
    context_hint: str | None = None
    image_base64: str | None = None


class InspectorAskResponse(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    abstained: bool = False
    sound_events: list[str] = Field(default_factory=list)
    model_used: str | None = None


class InspectorIngestResponse(BaseModel):
    modality: str
    filename: str
    extracted_preview: str
    char_count: int
    findings: list[Finding] = Field(default_factory=list)
    notes: str | None = None


class HealthResponse(BaseModel):
    status: str
    ollama_reachable: bool
    ollama_models: list[str] = Field(default_factory=list)
    offline_ready: bool