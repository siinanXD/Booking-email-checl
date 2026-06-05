"""Kurz-Zusammenfassung einer Mail für die Detailansicht."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class MailSummary(BaseModel):
    """Heuristische oder LLM-Zusammenfassung."""

    correlation_id: str
    summary_text: str = ""
    sentiment: str = "neutral"
    source: str = "heuristic"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
