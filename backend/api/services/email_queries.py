"""Email list and review queue queries."""

from __future__ import annotations

from math import ceil
from typing import Any

from backend.ai.domain.booking.booking_relevance import (
    classify_booking_mail,
    effective_booking_intent,
)
from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.services.mail_summary import MailSummaryService
from backend.api.schemas.emails import EmailDetail, EmailListItem, EmailListResponse
from backend.api.schemas.review import ReviewQueueItem
from backend.api.services.date_range import parse_date_range
from backend.core.config.factory import AppContext
from backend.core.models.email import StoredEmail
from backend.infrastructure.repositories.review_repository import ReviewRecord


class _EmailListContext:
    """Batch-geladene Extraktionen und Reviews für Listen-Queries."""

    __slots__ = ("extractions", "reviews")

    def __init__(
        self,
        extractions: dict[str, BookingExtraction],
        reviews: dict[str, ReviewRecord],
    ) -> None:
        self.extractions = extractions
        self.reviews = reviews


def _batch_email_list_context(
    ctx: AppContext,
    account_id: str,
    correlation_ids: list[str],
) -> _EmailListContext:
    return _EmailListContext(
        extractions=ctx.extraction_repo.map_by_correlation_ids(
            correlation_ids,
            account_id=account_id,
        ),
        reviews=ctx.review_repo.map_by_correlation_ids(
            correlation_ids,
            account_id=account_id,
        ),
    )


def _email_to_list_item(
    email: StoredEmail,
    batch: _EmailListContext,
) -> EmailListItem:
    ext = batch.extractions.get(email.correlation_id)
    review = batch.reviews.get(email.correlation_id)
    intent_val = effective_booking_intent(email, ext)
    intent_str = intent_val.value if intent_val else None
    return EmailListItem(
        correlation_id=email.correlation_id,
        message_id=email.message_id,
        subject=email.subject,
        from_address=email.from_address,
        received_at=email.received_at.isoformat() if email.received_at else None,
        platform=email.platform or (ext.platform if ext else None),
        intent=intent_str,
        booking_number=ext.booking_number if ext else None,
        processing_state=email.processing_state.value,
        review_status=review.review_status if review else None,
        grounding_flag=review.grounding_flag if review else False,
    )


def list_emails(
    ctx: AppContext,
    account_id: str,
    *,
    status: str | None,
    intent: str | None,
    intents: list[str] | None,
    platform: str | None,
    search: str | None,
    booking_related: bool,
    workflow_slug: str | None,
    page: int,
    limit: int,
    from_date: str | None = None,
    to_date: str | None = None,
) -> EmailListResponse:
    since_iso: str | None = None
    until_iso: str | None = None
    if from_date or to_date:
        since_iso, until_iso = parse_date_range(
            from_date=from_date,
            to_date=to_date,
        )
    if workflow_slug:
        return _list_emails_for_workflow(
            ctx,
            account_id,
            workflow_slug=workflow_slug.strip(),
            search=search,
            page=page,
            limit=limit,
        )
    fetch_limit = 500 if booking_related else limit
    fetch_page = 1 if booking_related else page
    intent_filter: list[str] = []
    if intents:
        intent_filter = intents
    elif intent:
        intent_filter = [intent]

    emails, total = ctx.email_repo.list_filtered(
        account_id=account_id,
        status=status,
        intent=None if booking_related else intent,
        intents=None if booking_related else intents,
        platform=platform,
        search=search,
        booking_related=booking_related,
        page=fetch_page,
        limit=fetch_limit,
        received_since=since_iso,
        received_until=until_iso,
    )
    if booking_related:
        batch = _batch_email_list_context(
            ctx,
            account_id,
            [email.correlation_id for email in emails],
        )
        strict: list[StoredEmail] = []
        for email in emails:
            ext = batch.extractions.get(email.correlation_id)
            if not classify_booking_mail(email, ext).is_booking:
                continue
            if intent_filter:
                eff = effective_booking_intent(email, ext)
                if eff is None or eff.value not in intent_filter:
                    continue
            strict.append(email)
        total = len(strict)
        offset = max(page - 1, 0) * limit
        emails = strict[offset : offset + limit]
        page_batch = _batch_email_list_context(
            ctx,
            account_id,
            [email.correlation_id for email in emails],
        )
        items = [_email_to_list_item(email, page_batch) for email in emails]
    else:
        page_batch = _batch_email_list_context(
            ctx,
            account_id,
            [email.correlation_id for email in emails],
        )
        items = [_email_to_list_item(email, page_batch) for email in emails]
    pages = ceil(total / limit) if limit else 0
    return EmailListResponse(items=items, total=total, page=page, pages=pages)


def _list_emails_for_workflow(
    ctx: AppContext,
    account_id: str,
    *,
    workflow_slug: str,
    search: str | None,
    page: int,
    limit: int,
) -> EmailListResponse:
    correlation_ids = ctx.extraction_repo.list_correlation_ids_by_workflow_slug(
        workflow_slug,
        account_id=account_id,
    )
    if not correlation_ids:
        return EmailListResponse(items=[], total=0, page=page, pages=0)
    emails = ctx.email_repo.list_by_correlation_ids(
        correlation_ids,
        account_id=account_id,
    )
    if search:
        needle = search.lower()
        emails = [
            e
            for e in emails
            if needle in e.subject.lower()
            or needle in e.from_address.lower()
            or needle in e.correlation_id.lower()
        ]
    matched = emails
    matched.sort(
        key=lambda e: e.received_at.timestamp() if e.received_at else 0,
        reverse=True,
    )
    total = len(matched)
    offset = max(page - 1, 0) * limit
    page_emails = matched[offset : offset + limit]
    page_batch = _batch_email_list_context(
        ctx,
        account_id,
        [email.correlation_id for email in page_emails],
    )
    items = [_email_to_list_item(email, page_batch) for email in page_emails]
    pages = ceil(total / limit) if limit else 0
    return EmailListResponse(items=items, total=total, page=page, pages=pages)


def get_email_detail(
    ctx: AppContext,
    account_id: str,
    correlation_id: str,
) -> EmailDetail | None:
    email = ctx.email_repo.get_by_correlation_id(
        correlation_id,
        account_id=account_id,
    )
    if email is None:
        return None
    ext = ctx.extraction_repo.get_by_correlation_id(
        correlation_id,
        account_id=account_id,
    )
    review = ctx.review_repo.get(correlation_id, account_id=account_id)
    extraction_json: dict[str, Any] | None = None
    if ext is not None:
        extraction_json = ext.model_dump(mode="json")
    summary_svc = MailSummaryService(ctx.mail_summary_repo)
    summary = summary_svc.get_or_create(
        email,
        ext,
        account_id=account_id,
    )
    return EmailDetail(
        correlation_id=email.correlation_id,
        message_id=email.message_id,
        subject=email.subject,
        from_address=email.from_address,
        to_addresses=email.to_addresses,
        body_text=email.body_text,
        received_at=email.received_at.isoformat() if email.received_at else None,
        platform=email.platform,
        intent=ext.intent.value if ext and ext.intent else None,
        booking_number=ext.booking_number if ext else None,
        processing_state=email.processing_state.value,
        review_status=review.review_status if review else None,
        grounding_flag=review.grounding_flag if review else False,
        draft_body=review.draft_body if review else "",
        extraction=extraction_json,
        approved_body=review.approved_body if review else None,
        mail_summary=summary.summary_text,
        mail_sentiment=summary.sentiment,
    )


def list_review_pending(
    ctx: AppContext,
    account_id: str,
    *,
    limit: int = 50,
) -> list[ReviewQueueItem]:
    from backend.api.services.review_queue_service import list_review_queue

    return list_review_queue(ctx, account_id, queue="pending", limit=limit)
