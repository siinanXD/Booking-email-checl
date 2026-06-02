"""Klassifikation via OpenAI SDK."""

from __future__ import annotations

from typing import Protocol, cast

from langfuse.decorators import langfuse_context, observe

from models.email import StoredEmail
from observability.alerts import AlertService
from observability.mail_cost import MailCostTracker
from schemas.booking.taxonomy import BookingIntent
from services.llm_errors import LLM_PIPELINE_ERRORS, notify_llm_failure
from services.llm_types import LLMCompletion
from services.prompt_loader import format_prompt_with_few_shots
from utils.pii import mask_pii


class LLMClient(Protocol):
    """Abstraktion für Tests."""

    def complete(self, prompt: str, model: str) -> LLMCompletion:
        """Return a completion for the supplied prompt and model."""
        ...


class ClassificationService:
    """Ordnet BookingIntent zu."""

    def __init__(
        self,
        llm: LLMClient,
        model: str,
        *,
        tracing: bool = False,
        alerts: AlertService | None = None,
        mail_cost: MailCostTracker | None = None,
    ) -> None:
        """Initialize the instance with its dependencies."""
        self._llm = llm
        self._model = model
        self._tracing = tracing
        self._alerts = alerts
        self._mail_cost = mail_cost

    def classify(self, email: StoredEmail) -> BookingIntent:
        """Klassifiziert eine gespeicherte Mail."""
        return cast(BookingIntent, self._classify_observed(email))

    @observe(
        name="classify",
        as_type="generation",
        capture_input=False,
        capture_output=False,
    )  # type: ignore[misc]
    def _classify_observed(self, email: StoredEmail) -> BookingIntent:
        if self._tracing:
            langfuse_context.update_current_trace(
                session_id=email.correlation_id,
                metadata={
                    "message_id": mask_pii(email.message_id),
                    "platform": email.platform,
                    "step": "classify",
                },
            )
            langfuse_context.update_current_observation(model=self._model)
        prompt = format_prompt_with_few_shots(
            "booking/classify.md",
            "booking/examples/classify_examples.json",
            subject=email.subject,
            from_address=email.from_address,
            body=email.body_text,
        )
        try:
            completion = self._llm.complete(prompt, self._model)
            self._record_cost(email.correlation_id, completion)
            slug = completion.text.strip().lower().replace(" ", "_")
            try:
                intent = BookingIntent(slug)
            except ValueError:
                intent = BookingIntent.OTHER
            if self._tracing:
                langfuse_context.update_current_trace(tags=[intent.value])
            return intent
        except LLM_PIPELINE_ERRORS as exc:
            notify_llm_failure(
                self._alerts,
                email.correlation_id,
                "classify",
                exc,
            )
            return BookingIntent.OTHER

    def _record_cost(self, correlation_id: str, completion: LLMCompletion) -> None:
        if self._mail_cost is not None:
            self._mail_cost.add(correlation_id, completion)
