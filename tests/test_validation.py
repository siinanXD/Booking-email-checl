"""Tests für Validierung."""

from __future__ import annotations

from datetime import date

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.ai.services.validation import ValidationService


def test_validate_dates_ok() -> None:
    """Verify validate dates ok."""
    ext = BookingExtraction(
        intent=BookingIntent.NEW_BOOKING,
        check_in=date(2026, 6, 12),
        check_out=date(2026, 6, 15),
    )
    result = ValidationService().validate(ext)
    assert result.valid is True


def test_validate_dates_invalid() -> None:
    """Verify validate dates invalid."""
    ext = BookingExtraction(
        check_in=date(2026, 6, 15),
        check_out=date(2026, 6, 12),
    )
    result = ValidationService().validate(ext)
    assert result.valid is False


def test_validate_new_booking_without_dates_ok() -> None:
    """Informelle Buchungsanfrage ohne feste Daten ist gültig."""
    ext = BookingExtraction(
        intent=BookingIntent.NEW_BOOKING,
        guest_name="Max Mustermann",
        email="max@example.com",
    )
    result = ValidationService().validate(ext)
    assert result.valid is True


def test_validate_cancellation_requires_booking_number() -> None:
    """Verify validate cancellation requires booking number."""
    ext = BookingExtraction(intent=BookingIntent.CANCELLATION)
    result = ValidationService().validate(ext)
    assert result.valid is False
