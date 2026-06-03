"""Grounding-Tests."""

from __future__ import annotations

from datetime import date

from backend.ai.services.grounding import GroundingService
from backend.ai.services.retrieval import RetrievalHits
from backend.core.models.entities import Guest, Reservation
from backend.core.models.response import GeneratedResponse


def _draft(body: str) -> GeneratedResponse:
    return GeneratedResponse(correlation_id="c1", body=body, model="test")


def test_grounding_ok_when_reference_known() -> None:
    """Verify grounding ok when reference known."""
    draft = _draft("Ihre Buchung AB100 ist bestätigt.")
    hits = RetrievalHits(
        reservations=[Reservation(reservation_id="r1", booking_number="AB100")]
    )
    assert GroundingService().check(draft, hits) is True


def test_grounding_fail_unknown_reference() -> None:
    """Verify grounding fail unknown reference."""
    draft = _draft("Buchung ZZ99999 wurde bearbeitet.")
    hits = RetrievalHits(
        reservations=[Reservation(reservation_id="r1", booking_number="AB100")]
    )
    result = GroundingService().check_with_detail(draft, hits)
    assert result.ok is False
    assert "booking_ref" in result.failed_fields
    assert GroundingService().check(draft, hits) is False


def test_grounding_fail_unknown_guest_name() -> None:
    """Verify grounding fail when draft mentions a name not in hits.guest."""
    draft = _draft("Sehr geehrter John Smith, Ihre Buchung AB100 ist bestätigt.")
    hits = RetrievalHits(
        guest=Guest(guest_id="g1", name="Anna Müller"),
        reservations=[Reservation(reservation_id="r1", booking_number="AB100")],
    )
    result = GroundingService().check_with_detail(draft, hits)
    assert result.ok is False
    assert "guest_name" in result.failed_fields


def test_grounding_fail_unknown_date() -> None:
    """Verify grounding fail when draft mentions a date not in reservations."""
    draft = _draft("Ihr Check-in am 2026-07-01 ist vorbereitet.")
    hits = RetrievalHits(
        reservations=[
            Reservation(
                reservation_id="r1",
                booking_number="AB100",
                check_in=date(2026, 6, 12),
                check_out=date(2026, 6, 15),
            )
        ]
    )
    result = GroundingService().check_with_detail(draft, hits)
    assert result.ok is False
    assert "date" in result.failed_fields


def test_grounding_fail_surname_only_overlap() -> None:
    """Verify partial surname overlap alone is not enough to pass."""
    draft = _draft("Sehr geehrter Herr Müller, Ihre Buchung AB100 ist bestätigt.")
    hits = RetrievalHits(
        guest=Guest(guest_id="g1", name="Max Müller"),
        reservations=[Reservation(reservation_id="r1", booking_number="AB100")],
    )
    result = GroundingService().check_with_detail(draft, hits)
    assert result.ok is False
    assert "guest_name" in result.failed_fields


def test_grounding_pass_all_facts_from_hits() -> None:
    """Verify grounding passes when booking, guest name and date match hits."""
    draft = _draft(
        "Sehr geehrte Anna Müller, Ihre Buchung AB100 "
        "vom 2026-06-12 bis 2026-06-15 ist bestätigt."
    )
    hits = RetrievalHits(
        guest=Guest(guest_id="g1", name="Anna Müller"),
        reservations=[
            Reservation(
                reservation_id="r1",
                booking_number="AB100",
                check_in=date(2026, 6, 12),
                check_out=date(2026, 6, 15),
            )
        ],
    )
    result = GroundingService().check_with_detail(draft, hits)
    assert result.ok is True
    assert result.failed_fields == []
    assert result.confidence == 1.0
