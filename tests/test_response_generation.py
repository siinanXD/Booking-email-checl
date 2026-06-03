"""Tests für Antwortgenerierung."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.ai.services.grounding import GroundingService
from backend.ai.services.response_generation import (
    ResponseGenerationService,
    _platform_tone,
)
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


def test_platform_tone_mapping() -> None:
    """Verify platform-specific tone instructions."""
    assert "informell" in _platform_tone("airbnb")
    assert "formell" in _platform_tone("booking.com")
    assert "formell" in _platform_tone("booking")
    assert "neutral" in _platform_tone(None)
    assert "neutral" in _platform_tone("expedia")


def test_build_prompt_includes_tone_and_grounding(
    entity_repo,
    email_repo,
) -> None:
    """Verify draft prompt contains platform tone and grounding instruction."""
    email = StoredEmail(
        message_id="draft-2",
        from_address="g@airbnb.com",
        subject="Frage",
        body_text="Wann Check-in?",
        received_at=datetime.now(UTC),
        correlation_id="corr-draft-2",
    )
    retrieval = RetrievalService(entity_repo, email_repo)
    svc = ResponseGenerationService(
        MockLLM(),
        "gpt-4o",
        retrieval,
        GroundingService(),
    )
    extraction = BookingExtraction(
        intent=BookingIntent.GUEST_INQUIRY,
        platform="airbnb",
    )
    prompt = svc._build_prompt(email, extraction, '{"guest": null}')
    assert "informell" in prompt
    assert "Erfinde keine Buchungsnummern" in prompt
    assert "Begrüßung" in prompt
    assert "Nächste Schritte" in prompt
