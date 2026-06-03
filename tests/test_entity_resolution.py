"""Tests für EntityResolutionService."""

from __future__ import annotations

from datetime import date

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.services.entity_resolution import (
    CONFIDENCE_BOOKING_NUMBER,
    CONFIDENCE_EMAIL_EXACT,
    CONFIDENCE_NAME_PLATFORM,
    EntityResolutionService,
)
from backend.core.models.entities import Guest, Reservation


def test_resolve_guest_exact_email(entity_repo) -> None:
    """Exakte E-Mail liefert Konfidenz 1.0."""
    entity_repo.upsert_guest(
        Guest(guest_id="g-email", email="relay@airbnb.com", name="Anna")
    )
    svc = EntityResolutionService(entity_repo)
    extraction = BookingExtraction(email="relay@airbnb.com")
    guest, confidence = svc.resolve_guest(extraction, "other@example.com")
    assert guest is not None
    assert guest.guest_id == "g-email"
    assert confidence == CONFIDENCE_EMAIL_EXACT


def test_resolve_guest_name_and_platform(entity_repo) -> None:
    """Gleicher Name + Plattform liefert Konfidenz 0.7."""
    entity_repo.upsert_guest(
        Guest(
            guest_id="g-name",
            name="Maria Schmidt",
            platform="airbnb",
            email="old@relay.airbnb.com",
        )
    )
    svc = EntityResolutionService(entity_repo)
    extraction = BookingExtraction(
        guest_name="maria schmidt",
        platform="airbnb",
    )
    guest, confidence = svc.resolve_guest(
        extraction,
        "abc123@relay.airbnb.com",
    )
    assert guest is not None
    assert guest.guest_id == "g-name"
    assert confidence == CONFIDENCE_NAME_PLATFORM


def test_resolve_guest_booking_number(entity_repo) -> None:
    """Buchungsnummer verknüpft über Reservierung → Konfidenz 0.9."""
    entity_repo.upsert_guest(
        Guest(guest_id="g-bn", email="hidden@relay.com", name="Tom")
    )
    entity_repo.upsert_reservation(
        Reservation(
            reservation_id="r-bn",
            guest_id="g-bn",
            booking_number="CHG42",
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 5),
        )
    )
    svc = EntityResolutionService(entity_repo)
    extraction = BookingExtraction(booking_number="CHG42")
    guest, confidence = svc.resolve_guest(extraction, "unknown@random.org")
    assert guest is not None
    assert guest.guest_id == "g-bn"
    assert confidence == CONFIDENCE_BOOKING_NUMBER


def test_resolve_guest_no_match_below_threshold(entity_repo) -> None:
    """Unbekannte Daten → kein Match, Konfidenz 0.0."""
    svc = EntityResolutionService(entity_repo)
    extraction = BookingExtraction(
        guest_name="Nobody",
        platform="airbnb",
    )
    guest, confidence = svc.resolve_guest(
        extraction,
        "unknown@random.org",
    )
    assert guest is None
    assert confidence == 0.0
