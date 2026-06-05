"""Robustheit bei LLM-/Netzwerkfehlern."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.ai.services.classification import ClassificationService
from backend.ai.services.extraction import ExtractionService
from backend.ai.services.grounding import GroundingService
from backend.ai.services.llm_types import LLMCompletion
from backend.ai.services.response_generation import ResponseGenerationService
from backend.ai.services.retrieval import RetrievalService
from backend.core.models.email import StoredEmail


class FailingLLM:
    """Test helper used by the suite."""

    def complete(
        self,
        prompt: str,
        model: str,
        *,
        temperature: float | None = None,
    ) -> LLMCompletion:
        """Execute the operation."""
        _ = temperature
        raise ConnectionError("simulated network failure")


def test_classify_returns_other_on_llm_failure() -> None:
    """Verify classify returns other on llm failure."""
    email = StoredEmail(
        message_id="fail-cls",
        from_address="g@airbnb.com",
        subject="Test",
        body_text="Body",
        received_at=datetime.now(UTC),
    )
    assert (
        ClassificationService(FailingLLM(), "gpt-4o-mini").classify(email)
        == BookingIntent.OTHER
    )


def test_extract_returns_low_confidence_on_llm_failure() -> None:
    """Verify extract returns low confidence on llm failure."""
    email = StoredEmail(
        message_id="fail-ext",
        from_address="g@airbnb.com",
        subject="Test",
        body_text="Body",
        received_at=datetime.now(UTC),
    )
    ext = ExtractionService(FailingLLM(), "gpt-4o-mini").extract(email)
    assert ext.confidence == 0.0


def test_generate_draft_fallback_on_llm_failure(
    entity_repo,
    email_repo,
) -> None:
    """Verify generate draft fallback on llm failure."""
    email = StoredEmail(
        message_id="fail-draft",
        from_address="g@test.com",
        subject="Test",
        body_text="Body",
        received_at=datetime.now(UTC),
        correlation_id="corr-fail-draft",
    )
    retrieval = RetrievalService(entity_repo, email_repo)
    draft = ResponseGenerationService(
        FailingLLM(),
        "gpt-4o",
        retrieval,
        GroundingService(),
    ).generate_draft(email, BookingExtraction())
    assert "guten tag" in draft.body.lower()
    assert "bitte prüfen" in draft.body.lower()
    assert draft.grounding_ok is False
