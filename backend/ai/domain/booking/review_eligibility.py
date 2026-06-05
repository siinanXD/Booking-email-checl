"""Welche Mails in die Human-Review-Queue gehören."""

from __future__ import annotations

from backend.ai.domain.booking.booking_relevance import classify_booking_mail
from backend.ai.domain.booking.extraction import BookingExtraction
from backend.core.models.email import StoredEmail


def is_custom_workflow_mail(*, workflow_id: str | None) -> bool:
    """Custom-Workflow-Mails haben kein Standard-Review in PR 4/5."""
    return bool(workflow_id and workflow_id.strip())


def is_review_queue_eligible(
    email: StoredEmail,
    extraction: BookingExtraction | None,
    *,
    workflow_id: str | None = None,
) -> tuple[bool, str | None]:
    """True wenn die Mail in /api/review/pending erscheinen darf."""
    if is_custom_workflow_mail(workflow_id=workflow_id):
        return False, "custom_workflow"
    verdict = classify_booking_mail(email, extraction)
    if not verdict.is_booking:
        return False, verdict.reason or "not_booking"
    return True, None
