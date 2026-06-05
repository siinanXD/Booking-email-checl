"""Tests für Review-Queue-Eligibility."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.review_eligibility import is_review_queue_eligible
from backend.core.models.email import StoredEmail


def test_custom_workflow_excluded() -> None:
    email = StoredEmail(
        message_id="m1",
        from_address="bookings@beds24.com",
        subject="Buchung",
        body_text="Body",
        received_at=datetime.now(UTC),
        correlation_id="c1",
    )
    ok, reason = is_review_queue_eligible(
        email,
        BookingExtraction(),
        workflow_id="wf-123",
    )
    assert ok is False
    assert reason == "custom_workflow"


def test_booking_mail_eligible() -> None:
    email = StoredEmail(
        message_id="m2",
        from_address="bookings@beds24.com",
        subject="Buchung: Zimmer 1",
        body_text="Buchung AB123",
        received_at=datetime.now(UTC),
        correlation_id="c2",
        platform="beds24",
    )
    ok, reason = is_review_queue_eligible(email, BookingExtraction())
    assert ok is True
    assert reason is None
