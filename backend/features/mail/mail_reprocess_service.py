"""Nachverarbeitung hängender Buchungs-Mails (z. B. nach Indexierungsfehler)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from backend.ai.domain.booking.booking_relevance import classify_booking_mail
from backend.ai.workflows.checkpointer import clear_thread_checkpoints
from backend.ai.workflows.email_workflow import EmailWorkflow
from backend.core.config.factory import AppContext
from backend.core.models.email import ProcessingState, StoredEmail
from backend.infrastructure.repositories.email_repository import EmailRepository
from backend.infrastructure.repositories.extraction_repository import (
    ExtractionRepository,
)
from backend.infrastructure.repositories.review_repository import ReviewRepository

logger = logging.getLogger(__name__)

_STUCK_STATES = frozenset(
    {
        ProcessingState.VALIDATED.value,
        ProcessingState.EXTRACTED.value,
        ProcessingState.CLASSIFIED.value,
        ProcessingState.RETRIEVED.value,
        ProcessingState.DRAFTED.value,
        ProcessingState.DISCARDED.value,
    }
)


@dataclass
class MailReprocessResult:
    """Ergebnis einer Nachverarbeitung."""

    attempted: int = 0
    completed: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


class MailReprocessService:
    """Setzt unterbrochene Workflows für Buchungs-Mails fort."""

    def __init__(
        self,
        email_repo: EmailRepository,
        extraction_repo: ExtractionRepository,
        review_repo: ReviewRepository,
        workflow: EmailWorkflow,
    ) -> None:
        self._email_repo = email_repo
        self._extraction_repo = extraction_repo
        self._review_repo = review_repo
        self._workflow = workflow

    def reprocess_stuck_bookings(
        self,
        account_id: str,
        *,
        limit: int = 25,
    ) -> MailReprocessResult:
        """Startet Workflow für Buchungs-Mails ohne ausstehenden Review neu."""
        result = MailReprocessResult()
        cursor = self._email_repo._col.find(
            {
                "account_id": account_id,
                "processing_state": {"$in": list(_STUCK_STATES)},
            }
        ).sort("updated_at", -1)

        for doc in cursor:
            if result.completed >= limit:
                break
            email = StoredEmail.from_mongo(doc)
            ext = self._extraction_repo.get_by_correlation_id(
                email.correlation_id,
                account_id=account_id,
            )
            if email.processing_state == ProcessingState.DISCARDED:
                triage = (email.triage_outcome or "").strip()
                if triage and triage != "not_booking_mail":
                    result.skipped += 1
                    continue
            if not classify_booking_mail(email, ext).is_booking:
                result.skipped += 1
                continue
            existing = self._review_repo.get(
                email.correlation_id,
                account_id=account_id,
            )
            if existing is not None and existing.review_status == "pending":
                result.skipped += 1
                continue
            result.attempted += 1
            try:
                clear_thread_checkpoints(
                    self._workflow._checkpointer,  # noqa: SLF001
                    email.correlation_id,
                )
                self._workflow.run(email, thread_id=email.correlation_id)
                result.completed += 1
            except Exception as exc:
                logger.exception(
                    "Reprocess failed for %s",
                    email.correlation_id,
                )
                result.errors.append(f"{email.correlation_id}: {exc}")
        return result


def build_mail_reprocess_service(ctx: AppContext) -> MailReprocessService:
    """Factory aus AppContext."""
    return MailReprocessService(
        ctx.email_repo,
        ctx.extraction_repo,
        ctx.review_repo,
        ctx.workflow,
    )
