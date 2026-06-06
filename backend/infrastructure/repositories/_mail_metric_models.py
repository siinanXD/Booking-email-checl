"""MailMetricRecord-Modell und Konvertierungshelfer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class MailMetricRecord(BaseModel):
    """Kosten-Snapshot einer Mail."""

    correlation_id: str
    cost_usd: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    account_id: str | None = None
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def record_from_doc(doc: dict[str, Any]) -> MailMetricRecord:
    """Konvertiert ein MongoDB-Dokument in ein MailMetricRecord."""
    payload = {k: v for k, v in doc.items() if k != "_id"}
    if "correlation_id" not in payload:
        payload["correlation_id"] = str(doc.get("_id", ""))
    processed = payload.get("processed_at")
    if isinstance(processed, str):
        payload["processed_at"] = datetime.fromisoformat(
            processed.replace("Z", "+00:00")
        )
    return MailMetricRecord.model_validate(payload)
