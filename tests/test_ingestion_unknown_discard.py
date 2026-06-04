"""Ingestion verwirft unbekannte irrelevante Mails."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.ai.services.ingestion import IngestionService
from backend.ai.services.triage import TriageService
from backend.core.models.email import IncomingEmail, ProcessingState
from backend.infrastructure.repositories.email_repository import EmailRepository


def test_ingest_discards_unknown_without_signals(
    email_repo: EmailRepository,
) -> None:
    """UNKNOWN-Domain ohne Signale landet als DISCARDED."""
    payload = IncomingEmail(
        message_id="msg-unknown-discard@random.org",
        from_address="unknown@random.org",
        subject="Hello",
        body_text="Generic inquiry",
        received_at=datetime.now(UTC),
    )
    svc = IngestionService(email_repo, TriageService(triage_llm_enabled=False))
    result = svc.ingest(payload)
    assert result.discarded is True
    assert result.email.processing_state == ProcessingState.DISCARDED
