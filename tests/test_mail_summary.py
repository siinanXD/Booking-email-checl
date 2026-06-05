"""Tests für MailSummaryService."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.ai.services.mail_summary import MailSummaryService
from backend.core.models.email import StoredEmail
from backend.infrastructure.repositories.mail_summary_repository import (
    MailSummaryRepository,
)


def test_heuristic_summary(mock_db: object) -> None:
    repo = MailSummaryRepository(mock_db)  # type: ignore[arg-type]
    svc = MailSummaryService(repo)
    email = StoredEmail(
        message_id="m1",
        from_address="bookings@beds24.com",
        subject="Buchung",
        body_text="Danke für die Buchung",
        received_at=datetime.now(UTC),
        correlation_id="c-sum",
        account_id="acc-1",
    )
    ext = BookingExtraction(
        intent=BookingIntent.NEW_BOOKING,
        guest_name="Max",
        booking_number="AB1",
    )
    summary = svc.get_or_create(email, ext, account_id="acc-1")
    assert "Neue Buchung" in summary.summary_text
    assert summary.correlation_id == "c-sum"
