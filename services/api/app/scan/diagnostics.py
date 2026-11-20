"""Structured scan diagnostics (request id + stage timings)."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("airlock.scan")


@dataclass
class ScanDiagnostics:
    request_id: str
    action_id: str
    modality: str
    filename: str
    stages_ms: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @contextmanager
    def stage(self, name: str):
        t0 = time.perf_counter()
        try:
            yield
        finally:
            ms = (time.perf_counter() - t0) * 1000
            self.stages_ms[name] = round(ms, 1)
            logger.info(
                "scan_stage request_id=%s action_id=%s stage=%s ms=%.1f",
                self.request_id,
                self.action_id,
                name,
                ms,
            )

    def note(self, msg: str) -> None:
        self.notes.append(msg)
        logger.warning(
            "scan_note request_id=%s action_id=%s %s",
            self.request_id,
            self.action_id,
            msg,
        )

    def to_meta(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "stages_ms": self.stages_ms,
            "notes": self.notes,
        }


def new_scan_diag(action_id: str, modality: str, filename: str) -> ScanDiagnostics:
    rid = f"scanreq-{uuid.uuid4().hex[:10]}"
    logger.info(
        "scan_start request_id=%s action_id=%s modality=%s file=%s",
        rid,
        action_id,
        modality,
        filename,
    )
    return ScanDiagnostics(rid, action_id, modality, filename)