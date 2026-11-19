import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.models import Finding, IncidentDetail, IncidentSummary
from app.settings import settings

_engine: Engine | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            f"sqlite:///{settings.db_path}",
            connect_args={"check_same_thread": False},
        )
        init_db(_engine)
    return _engine


def init_db(engine: Engine) -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS incidents (
          id TEXT PRIMARY KEY,
          action_id TEXT NOT NULL UNIQUE,
          observed_at TEXT NOT NULL,
          source_type TEXT NOT NULL,
          source_app TEXT,
          destination_origin TEXT,
          modality TEXT NOT NULL,
          severity TEXT NOT NULL,
          decision TEXT NOT NULL,
          workflow_state TEXT NOT NULL,
          outcome TEXT NOT NULL,
          transmission_status TEXT NOT NULL DEFAULT 'unknown',
          review_status TEXT NOT NULL DEFAULT 'pending',
          title TEXT NOT NULL,
          summary_redacted TEXT,
          payload_sha256 TEXT,
          scan_duration_ms INTEGER,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS findings (
          id TEXT PRIMARY KEY,
          incident_id TEXT NOT NULL,
          category TEXT NOT NULL,
          severity TEXT NOT NULL,
          detector TEXT NOT NULL,
          confidence_label TEXT,
          anchor_json TEXT NOT NULL,
          excerpt_redacted TEXT,
          policy_rule_id TEXT,
          explanation_redacted TEXT,
          is_confirmed INTEGER NOT NULL DEFAULT 0
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS event_steps (
          id TEXT PRIMARY KEY,
          incident_id TEXT NOT NULL,
          occurred_at TEXT NOT NULL,
          step TEXT NOT NULL,
          details_json TEXT
        )
        """,
    ]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def _next_incident_id(conn) -> str:
    row = conn.execute(text("SELECT COUNT(*) AS c FROM incidents")).mappings().one()
    return f"AL-{int(row['c']) + 1:04d}"


def create_incident_from_scan(
    *,
    action_id: str,
    modality: str,
    severity: str,
    decision: str,
    title: str,
    summary_redacted: str | None,
    destination_origin: str,
    source_app: str,
    findings: list[Finding],
    payload_sha256: str,
) -> str:
    engine = get_engine()
    now = _now_iso()
    workflow = "review_required" if decision in ("require_review", "block", "unknown") else "allowed"
    outcome = "pending_review" if workflow == "review_required" else "allowed"
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT id FROM incidents WHERE action_id = :aid"),
            {"aid": action_id},
        ).mappings().first()
        if existing:
            incident_id = existing["id"]
            conn.execute(
                text(
                    """
                    UPDATE incidents SET severity=:sev, decision=:dec, workflow_state=:wf,
                    outcome=:out, title=:title, summary_redacted=:sum, updated_at=:now,
                    payload_sha256=:sha
                    WHERE id=:id
                    """
                ),
                {
                    "sev": severity,
                    "dec": decision,
                    "wf": workflow,
                    "out": outcome,
                    "title": title,
                    "sum": summary_redacted,
                    "now": now,
                    "sha": payload_sha256,
                    "id": incident_id,
                },
            )
            conn.execute(text("DELETE FROM findings WHERE incident_id = :id"), {"id": incident_id})
        else:
            incident_id = _next_incident_id(conn)
            conn.execute(
                text(
                    """
                    INSERT INTO incidents (
                      id, action_id, observed_at, source_type, source_app, destination_origin,
                      modality, severity, decision, workflow_state, outcome, transmission_status,
                      review_status, title, summary_redacted, payload_sha256, created_at, updated_at
                    ) VALUES (
                      :id, :aid, :obs, 'browser_extension', :src, :dest,
                      :mod, :sev, :dec, :wf, :out, 'not_sent_confirmed',
                      'pending', :title, :sum, :sha, :now, :now
                    )
                    """
                ),
                {
                    "id": incident_id,
                    "aid": action_id,
                    "obs": now,
                    "src": source_app,
                    "dest": destination_origin,
                    "mod": modality,
                    "sev": severity,
                    "dec": decision,
                    "wf": workflow,
                    "out": outcome,
                    "title": title,
                    "sum": summary_redacted,
                    "sha": payload_sha256,
                    "now": now,
                },
            )

        for f in findings:
            conn.execute(
                text(
                    """
                    INSERT INTO findings (
                      id, incident_id, category, severity, detector, confidence_label,
                      anchor_json, excerpt_redacted, policy_rule_id, explanation_redacted
                    ) VALUES (
                      :id, :iid, :cat, :sev, :det, :conf, :anchor, :exc, :pol, :exp
                    )
                    """
                ),
                {
                    "id": f.id,
                    "iid": incident_id,
                    "cat": f.category,
                    "sev": f.severity,
                    "det": f.detector,
                    "conf": f.confidence_label,
                    "anchor": json.dumps(f.anchor.model_dump()),
                    "exc": f.excerpt_redacted,
                    "pol": f.policy_rule_id,
                    "exp": f.explanation_redacted,
                },
            )
    return incident_id


def add_event_step(incident_id: str, step: str, details: dict | None = None) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO event_steps (id, incident_id, occurred_at, step, details_json)
                VALUES (:id, :iid, :at, :step, :det)
                """
            ),
            {
                "id": f"step-{uuid.uuid4().hex[:12]}",
                "iid": incident_id,
                "at": _now_iso(),
                "step": step,
                "det": json.dumps(details or {}),
            },
        )


def list_incidents(limit: int = 50) -> list[IncidentSummary]:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, action_id, observed_at, modality, severity, decision,
                       workflow_state, outcome, transmission_status, review_status,
                       title, summary_redacted
                FROM incidents ORDER BY observed_at DESC LIMIT :lim
                """
            ),
            {"lim": limit},
        ).mappings().all()
    return [IncidentSummary(**dict(r)) for r in rows]


def get_incident(incident_id: str) -> IncidentDetail | None:
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM incidents WHERE id = :id"),
            {"id": incident_id},
        ).mappings().first()
        if not row:
            return None
        findings_rows = conn.execute(
            text("SELECT * FROM findings WHERE incident_id = :id"),
            {"id": incident_id},
        ).mappings().all()
        steps = conn.execute(
            text(
                "SELECT step, occurred_at, details_json FROM event_steps WHERE incident_id = :id ORDER BY occurred_at"
            ),
            {"id": incident_id},
        ).mappings().all()

    findings: list[Finding] = []
    for fr in findings_rows:
        anchor = json.loads(fr["anchor_json"])
        findings.append(
            Finding(
                id=fr["id"],
                category=fr["category"],
                severity=fr["severity"],
                detector=fr["detector"],
                confidence_label=fr["confidence_label"],
                anchor=anchor,
                excerpt_redacted=fr["excerpt_redacted"] or "",
                explanation_redacted=fr["explanation_redacted"] or "",
                policy_rule_id=fr["policy_rule_id"],
            )
        )

    steps_out = [
        {"step": s["step"], "occurred_at": s["occurred_at"], "details": json.loads(s["details_json"] or "{}")}
        for s in steps
    ]

    base = {k: row[k] for k in IncidentSummary.model_fields}
    return IncidentDetail(**base, findings=findings, event_steps=steps_out)


def analytics_summary() -> dict:
    engine = get_engine()
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) AS c FROM incidents")).scalar() or 0
        review = conn.execute(
            text("SELECT COUNT(*) AS c FROM incidents WHERE decision = 'require_review'")
        ).scalar() or 0
        prevented = conn.execute(
            text(
                "SELECT COUNT(*) AS c FROM incidents WHERE transmission_status = 'not_sent_confirmed' AND outcome = 'pending_review'"
            )
        ).scalar() or 0
        by_mod = conn.execute(
            text("SELECT modality, COUNT(*) AS c FROM incidents GROUP BY modality")
        ).mappings().all()
    return {
        "actions_scanned": int(total),
        "review_required": int(review),
        "prevented": int(prevented),
        "by_modality": {r["modality"]: int(r["c"]) for r in by_mod},
    }


def update_triage(incident_id: str, review_status: str, resolution: str | None = None) -> bool:
    engine = get_engine()
    now = _now_iso()
    outcome = "false_positive" if review_status == "false_positive" else "resolved"
    with engine.begin() as conn:
        res = conn.execute(
            text(
                """
                UPDATE incidents SET review_status=:rs, outcome=:out, updated_at=:now WHERE id=:id
                """
            ),
            {"rs": review_status, "out": outcome, "now": now, "id": incident_id},
        )
        return res.rowcount > 0