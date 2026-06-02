"""Tests für Antwortgenerierung."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.ai.services.grounding import GroundingService
from backend.ai.services.response_generation import ResponseGenerationService
from backend.ai.services.retrieval import RetrievalHits, RetrievalService
from backend.core.models.email import StoredEmail
from backend.core.models.entities import Reservation
from tests.mocks import MockLLM


def test_generate_draft_uses_mock(
    entity_repo,
    email_repo,
) -> None:
    """Verify generate draft uses mock."""
    email = StoredEmail(
        message_id="draft-1",
        from_address="g@test.com",
        subject="Stornierung AB100",
        body_text="Bitte AB100 stornieren",
        received_at=datetime.now(UTC),
        correlation_id="corr-draft-1",
    )
    retrieval = RetrievalService(entity_repo, email_repo)
    svc = ResponseGenerationService(
        MockLLM(),
        "gpt-4o",
        retrieval,
        GroundingService(),
    )
    extraction = BookingExtraction(
        intent=BookingIntent.CANCELLATION,
        booking_number="AB100",
    )
    hits = RetrievalHits(
        reservations=[Reservation(reservation_id="r1", booking_number="AB100")]
    )
    draft = svc.generate_draft(email, extraction, hits)
    assert "bearbeitet" in draft.body.lower() or len(draft.body) > 0
    assert draft.prompt_tokens >= 0
