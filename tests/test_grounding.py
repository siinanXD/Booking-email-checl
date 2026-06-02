"""Grounding-Tests."""

from __future__ import annotations

from backend.ai.services.grounding import GroundingService
from backend.ai.services.retrieval import RetrievalHits
from backend.core.models.entities import Reservation
from backend.core.models.response import GeneratedResponse


def test_grounding_ok_when_reference_known() -> None:
    """Verify grounding ok when reference known."""
    draft = GeneratedResponse(
        correlation_id="c1",
        body="Ihre Buchung AB100 ist bestätigt.",
        model="test",
    )
    hits = RetrievalHits(
        reservations=[Reservation(reservation_id="r1", booking_number="AB100")]
    )
    assert GroundingService().check(draft, hits) is True


def test_grounding_fail_unknown_reference() -> None:
    """Verify grounding fail unknown reference."""
    draft = GeneratedResponse(
        correlation_id="c2",
        body="Buchung ZZ99999 wurde bearbeitet.",
        model="test",
    )
    hits = RetrievalHits(
        reservations=[Reservation(reservation_id="r1", booking_number="AB100")]
    )
    assert GroundingService().check(draft, hits) is False
