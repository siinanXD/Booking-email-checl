"""Review-Warteschlangen (pending, released, completed)."""

from __future__ import annotations

from backend.ai.domain.booking.review_eligibility import is_review_queue_eligible
from backend.api.schemas.review import ReviewQueueItem
from backend.api.services.review_list_support import record_to_queue_item_from_maps
from backend.core.config.factory import AppContext

_STATUS_PENDING = ("pending",)
_STATUS_RELEASED = ("approved",)
_STATUS_COMPLETED = ("completed",)


def count_eligible_pending_reviews(ctx: AppContext, account_id: str) -> int:
    """Zählt ausstehende, review-eligible Buchungs-Mails."""
    records = ctx.review_repo.list_by_status(
        _STATUS_PENDING,
        limit=500,
        account_id=account_id,
    )
    if not records:
        return 0
    correlation_ids = [record.correlation_id for record in records]
    emails = {
        email.correlation_id: email
        for email in ctx.email_repo.list_by_correlation_ids(
            correlation_ids,
            account_id=account_id,
        )
    }
    snapshots = ctx.extraction_repo.map_snapshots_by_correlation_ids(
        correlation_ids,
        account_id=account_id,
    )
    count = 0
    for record in records:
        email = emails.get(record.correlation_id)
        if email is None:
            continue
        snap = snapshots.get(record.correlation_id)
        ext = snap.extraction if snap else None
        workflow_id = snap.workflow_id if snap else None
        eligible, _ = is_review_queue_eligible(
            email,
            ext,
            workflow_id=workflow_id,
        )
        if eligible:
            count += 1
    return count


def list_review_queue(
    ctx: AppContext,
    account_id: str,
    *,
    queue: str,
    limit: int = 50,
    intent: str | None = None,
    grounding_only: bool = False,
) -> list[ReviewQueueItem]:
    """Lädt Review-Liste nach Tab (pending | released | completed)."""
    statuses: tuple[str, ...]
    if grounding_only:
        statuses = ("pending", "approved")
    else:
        statuses = _statuses_for_queue(queue)
    fetch_limit = min(max(limit, 1), 100) * (8 if grounding_only else 4)
    records = ctx.review_repo.list_by_status(
        statuses,
        limit=fetch_limit,
        account_id=account_id,
        grounding_only=grounding_only,
    )
    if not records:
        return []

    correlation_ids = [record.correlation_id for record in records]
    emails = {
        email.correlation_id: email
        for email in ctx.email_repo.list_by_correlation_ids(
            correlation_ids,
            account_id=account_id,
        )
    }
    snapshots = ctx.extraction_repo.map_snapshots_by_correlation_ids(
        correlation_ids,
        account_id=account_id,
    )

    items: list[ReviewQueueItem] = []
    for record in records:
        snap = snapshots.get(record.correlation_id)
        item = record_to_queue_item_from_maps(
            record,
            email=emails.get(record.correlation_id),
            ext=snap.extraction if snap else None,
            workflow_id=snap.workflow_id if snap else None,
            allow_ineligible=grounding_only,
        )
        if item is None:
            continue
        if intent and (item.intent or "") != intent:
            continue
        items.append(item)
        if len(items) >= limit:
            break
    return items


def _statuses_for_queue(queue: str) -> tuple[str, ...]:
    normalized = (queue or "pending").strip().lower()
    if normalized in ("released", "approved"):
        return _STATUS_RELEASED
    if normalized == "completed":
        return _STATUS_COMPLETED
    return _STATUS_PENDING
