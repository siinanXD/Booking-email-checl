"""Human-Review-Schnittstelle."""

from __future__ import annotations

from typing import Any, Protocol

from workflows.email_workflow import EmailWorkflow


class ReviewPort(Protocol):
    """Freigabe nach LangGraph-Interrupt."""

    def approve_draft(
        self,
        correlation_id: str,
        approved_body: str | None = None,
    ) -> dict[str, Any]:
        """Approve the pending draft."""
        ...

    def reject_draft(
        self,
        correlation_id: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Reject the pending draft."""
        ...


class ReviewRouter:
    """Resume des Workflows nach menschlicher Freigabe."""

    def __init__(self, workflow: EmailWorkflow) -> None:
        """Initialize the instance with its dependencies."""
        self._workflow = workflow

    def approve_draft(
        self,
        correlation_id: str,
        approved_body: str | None = None,
    ) -> dict[str, Any]:
        """Setzt den Workflow nach Freigabe fort."""
        return self._workflow.resume_after_approval(
            thread_id=correlation_id,
            approved_body=approved_body,
        )

    def reject_draft(
        self,
        correlation_id: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Lehnt den Entwurf ab (kein Versand)."""
        return self._workflow.resume_after_rejection(
            thread_id=correlation_id,
            reason=reason,
        )
