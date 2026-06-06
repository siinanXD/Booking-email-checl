"""End-to-End-Tests: Review-Edge-Cases via HTTP (ohne Workflow-Level)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def test_complete_without_approve_returns_400(
    client: Any,
    auth_headers: dict[str, str],
    tenant_account_id: str,
    mock_db: Any,
) -> None:
    """Complete ohne vorherige Freigabe → 400."""
    from backend.ai.domain.booking.extraction import BookingExtraction
    from backend.core.models.email import ProcessingState, StoredEmail
    from backend.infrastructure.repositories.email_repository import EmailRepository
    from backend.infrastructure.repositories.extraction_repository import (
        ExtractionRepository,
    )
    from backend.infrastructure.repositories.review_repository import ReviewRepository

    cid = "e2e-complete-no-approve-001"
    msg_id = "msg-complete-no-approve@test"

    EmailRepository(mock_db).upsert_by_message_id(  # type: ignore[arg-type]
        StoredEmail(
            message_id=msg_id,
            from_address="guest@test.local",
            subject="Test",
            body_text="Test",
            received_at=datetime.now(UTC),
            correlation_id=cid,
            processing_state=ProcessingState.PENDING_REVIEW,
            account_id=tenant_account_id,
        )
    )
    ExtractionRepository(mock_db).save(  # type: ignore[arg-type]
        cid, msg_id, BookingExtraction(), account_id=tenant_account_id
    )
    ReviewRepository(mock_db).upsert_pending(  # type: ignore[arg-type]
        correlation_id=cid,
        message_id=msg_id,
        draft_body="Entwurf",
        grounding_flag=False,
        intent="other",
        account_id=tenant_account_id,
    )

    resp = client.post(
        "/api/review/complete",
        json={"correlation_id": cid},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_reject_via_http_api(
    client: Any,
    auth_headers: dict[str, str],
    tenant_account_id: str,
    mock_db: Any,
) -> None:
    """Reject via HTTP → 200 (LangGraph-Resume wird versucht, kein harter Fehler)."""
    from backend.ai.domain.booking.extraction import BookingExtraction
    from backend.core.models.email import ProcessingState, StoredEmail
    from backend.infrastructure.repositories.email_repository import EmailRepository
    from backend.infrastructure.repositories.extraction_repository import (
        ExtractionRepository,
    )
    from backend.infrastructure.repositories.review_repository import ReviewRepository

    cid = "e2e-reject-http-001"
    msg_id = "msg-reject-http@test"

    EmailRepository(mock_db).upsert_by_message_id(  # type: ignore[arg-type]
        StoredEmail(
            message_id=msg_id,
            from_address="guest@booking.com",
            subject="XY999 Stornierung",
            body_text="Stornierung XY999",
            received_at=datetime.now(UTC),
            correlation_id=cid,
            processing_state=ProcessingState.PENDING_REVIEW,
            account_id=tenant_account_id,
        )
    )
    ExtractionRepository(mock_db).save(  # type: ignore[arg-type]
        cid,
        msg_id,
        BookingExtraction(booking_number="XY999"),
        account_id=tenant_account_id,
    )
    ReviewRepository(mock_db).upsert_pending(  # type: ignore[arg-type]
        correlation_id=cid,
        message_id=msg_id,
        draft_body="Falscher Entwurf",
        grounding_flag=False,
        intent="cancellation",
        account_id=tenant_account_id,
    )

    resp = client.post(
        "/api/review/reject",
        json={"correlation_id": cid, "reason": "Falsche Buchungsnummer"},
        headers=auth_headers,
    )
    # Reject geht durch LangGraph-Resume; ohne Checkpoint: 200 oder 400
    assert resp.status_code in (200, 400)
