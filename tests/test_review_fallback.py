"""Tests für review_fallback."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.ai.services.review_fallback import fallback_draft_body
from backend.core.models.email import StoredEmail


def test_fallback_contains_guest() -> None:
    email = StoredEmail(
        message_id="m1",
        from_address="g@test.com",
        subject="Frage",
        body_text="Body",
        received_at=datetime.now(UTC),
        correlation_id="c1",
    )
    body = fallback_draft_body(
        email,
        BookingExtraction(
            intent=BookingIntent.GUEST_INQUIRY,
            guest_name="Anna",
            booking_number="AB99",
        ),
    )
    assert "Anna" in body
    assert "AB99" in body
