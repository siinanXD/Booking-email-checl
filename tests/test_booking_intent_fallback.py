"""Tests für Beds24-Intent-Fallback und Buchungslisten."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.ai.domain.booking.booking_relevance import (
    effective_booking_intent,
    infer_beds24_intent,
)
from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.core.models.email import ProcessingState, StoredEmail


def test_infer_beds24_intent_from_subject() -> None:
    assert infer_beds24_intent("Buchung: Zimmer 1") == BookingIntent.NEW_BOOKING
    assert infer_beds24_intent("Stornierung: Zimmer 2") == BookingIntent.CANCELLATION
    assert infer_beds24_intent("Buchungsänderung: Zimmer 3") == BookingIntent.CHANGE


def test_effective_intent_prefers_extraction_over_other() -> None:
    email = StoredEmail(
        message_id="m1",
        from_address="bookings@beds24.com",
        subject="Buchung: Test",
        body_text="",
        received_at=datetime.now(UTC),
        correlation_id="c1",
        processing_state=ProcessingState.VALIDATED,
    )
    ext = BookingExtraction(intent=BookingIntent.OTHER)
    assert effective_booking_intent(email, ext) == BookingIntent.NEW_BOOKING
