"""Routing helpers for the email workflow graph."""

from __future__ import annotations

from typing import Literal

from backend.ai.domain.booking.booking_relevance import classify_booking_mail
from backend.ai.workflows.state import EmailWorkflowState
from backend.core.models.email import ProcessingState
from backend.infrastructure.observability.alerts import AlertService
from backend.infrastructure.repositories.email_repository import EmailRepository


def after_ingest(state: EmailWorkflowState) -> Literal["end", "classify"]:
    if state.get("ingest_discarded"):
        return "end"
    return "classify"


def after_validate(
    state: EmailWorkflowState,
    *,
    email_repo: EmailRepository,
    alerts: AlertService | None,
) -> Literal["end", "retrieve"]:
    errors = state.get("validation_errors") or []
    email = state["email"]
    if errors:
        if alerts:
            alerts.check_extraction_failure(
                email.correlation_id,
                "; ".join(errors),
            )
        return "end"
    extraction = state.get("extraction")
    if not classify_booking_mail(email, extraction).is_booking:
        email_repo.update_processing_state(
            email.message_id,
            ProcessingState.DISCARDED,
            account_id=email.account_id,
            triage_outcome="not_booking_mail",
        )
        return "end"
    return "retrieve"
