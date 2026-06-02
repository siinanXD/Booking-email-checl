"""Antwortentwurf mit Grounding."""

from __future__ import annotations

import json
from typing import cast

from langfuse.decorators import langfuse_context, observe

from models.email import StoredEmail
from models.response import GeneratedResponse
from observability.alerts import AlertService
from observability.mail_cost import MailCostTracker
from schemas.booking.extraction import BookingExtraction
from services.classification import LLMClient
from services.grounding import GroundingService
from services.llm_errors import LLM_PIPELINE_ERRORS, notify_llm_failure
from services.prompt_loader import format_prompt
from services.retrieval import RetrievalHits, RetrievalService
from utils.pii import mask_pii

_FALLBACK_DRAFT_BODY = (
    "[Automatischer Entwurf fehlgeschlagen. Bitte manuell antworten.]"
)


class ResponseGenerationService:
    """Erzeugt Antwortentwürfe aus Retrieval-Kontext."""

    def __init__(
        self,
        llm: LLMClient,
        model: str,
        retrieval: RetrievalService,
        grounding: GroundingService | None = None,
        *,
        tracing: bool = False,
        alerts: AlertService | None = None,
        mail_cost: MailCostTracker | None = None,
    ) -> None:
        self._llm = llm
        self._model = model
        self._retrieval = retrieval
        self._grounding = grounding or GroundingService()
        self._tracing = tracing
        self._alerts = alerts
        self._mail_cost = mail_cost

    def generate_draft(
        self,
        email: StoredEmail,
        extraction: BookingExtraction,
        hits: RetrievalHits | None = None,
    ) -> GeneratedResponse:
        """Erstellt Entwurf und prüft Grounding."""
        return cast(
            GeneratedResponse,
            self._generate_draft_observed(email, extraction, hits),
        )

    @observe(name="draft_response", as_type="generation")  # type: ignore[misc]
    def _generate_draft_observed(
        self,
        email: StoredEmail,
        extraction: BookingExtraction,
        hits: RetrievalHits | None,
    ) -> GeneratedResponse:
        if self._tracing:
            langfuse_context.update_current_trace(
                session_id=email.correlation_id,
                metadata={
                    "message_id": mask_pii(email.message_id),
                    "step": "draft",
                },
            )
            langfuse_context.update_current_observation(model=self._model)
        if hits is None:
            hits = self._retrieval.retrieve(email, extraction)
        facts = self._facts_json(hits, extraction)
        prompt = format_prompt(
            "booking/draft.md",
            facts=facts,
            body=email.body_text,
        )
        try:
            completion = self._llm.complete(prompt, self._model)
            if self._mail_cost is not None:
                self._mail_cost.add(email.correlation_id, completion)
            draft = GeneratedResponse(
                correlation_id=email.correlation_id,
                body=completion.text,
                model=self._model,
                prompt_tokens=completion.prompt_tokens,
                completion_tokens=completion.completion_tokens,
            )
        except LLM_PIPELINE_ERRORS as exc:
            notify_llm_failure(
                self._alerts,
                email.correlation_id,
                "draft_response",
                exc,
            )
            draft = GeneratedResponse(
                correlation_id=email.correlation_id,
                body=_FALLBACK_DRAFT_BODY,
                model=self._model,
                grounding_ok=False,
            )
            return draft
        draft.grounding_ok = self._grounding.check(draft, hits)
        return draft

    def _facts_json(
        self,
        hits: RetrievalHits,
        extraction: BookingExtraction,
    ) -> str:
        payload = {
            "extraction": extraction.model_dump(mode="json"),
            "reservations": [
                r.model_dump(mode="json") for r in (hits.reservations or [])
            ],
            "guest": hits.guest.model_dump(mode="json") if hits.guest else None,
            "similar_cases": hits.similar_cases or [],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
