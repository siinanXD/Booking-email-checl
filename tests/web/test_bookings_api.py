"""Buchungslisten-API."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.core.models.email import ProcessingState, StoredEmail
from backend.infrastructure.repositories.extraction_repository import (
    ExtractionRepository,
)


def test_list_bookings(
    client: Any,
    auth_headers: dict[str, str],
    tenant_account_id: str,
    email_repo: Any,
    extraction_repo: ExtractionRepository,
) -> None:
    """GET /api/bookings liefert new_booking mit Extraktion."""
    cid = "corr-booking-api"
    email_repo.upsert_by_message_id(
        StoredEmail(
            message_id="m-booking@test",
            from_address="bookings@beds24.com",
            subject="Neue Buchung AB99",
            body_text="Reservierung bestätigt",
            received_at=datetime.now(UTC),
            correlation_id=cid,
            processing_state=ProcessingState.CLASSIFIED,
            platform="beds24",
            account_id=tenant_account_id,
        )
    )
    extraction_repo.save(
        cid,
        "m-booking@test",
        BookingExtraction(intent=BookingIntent.NEW_BOOKING, booking_number="AB99"),
        account_id=tenant_account_id,
    )
    resp = client.get("/api/bookings/?limit=20", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] >= 1
    assert any(item["correlation_id"] == cid for item in data["items"])
