"""Tests für extraction_enrichment."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.extraction_enrichment import enrich_extraction
from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.core.models.email import StoredEmail


def test_enrich_guest_from_subject() -> None:
    email = StoredEmail(
        message_id="m1",
        from_address="a@b.com",
        subject="Nachricht vom Gast - Max Mustermann",
        body_text="Hi",
        received_at=datetime.now(UTC),
        correlation_id="c1",
        platform="beds24",
    )
    ext = enrich_extraction(email, BookingExtraction())
    assert ext.guest_name == "Max Mustermann"
    assert ext.platform == "beds24"


def test_enrich_informal_booking_intent_and_property_match() -> None:
    email = StoredEmail(
        message_id="m2",
        from_address="noreply@host.com",
        subject="Anfrage",
        body_text="ich würde gerne diese Buchung tätigen\nName: Anna",
        received_at=datetime.now(UTC),
        correlation_id="c2",
    )
    ext = enrich_extraction(
        email,
        BookingExtraction(
            intent=BookingIntent.GUEST_INQUIRY, property_name="Ferienhaus Nord"
        ),
        known_property_names=["Ferienhaus Nord", "Studio Süd"],
    )
    assert ext.intent == BookingIntent.NEW_BOOKING
    assert ext.property_name == "Ferienhaus Nord"
    assert ext.guest_name == "Anna"
