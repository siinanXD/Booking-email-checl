"""Email list and review queue queries."""

from __future__ import annotations

from math import ceil
from typing import Any

from backend.ai.domain.booking.booking_relevance import (
    classify_booking_mail,
    effective_booking_intent,
)
from backend.api.schemas.emails import EmailDetail, EmailListItem, EmailListResponse
from backend.api.schemas.review import ReviewQueueItem
from backend.core.config.factory import AppContext
from backend.core.models.email import StoredEmail


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
    page: int,
    limit: int,
) -> EmailListResponse:
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
    )
    if booking_related:
        strict: list[StoredEmail] = []
        for email in emails:
            ext = ctx.extraction_repo.get_by_correlation_id(
                email.correlation_id,
                account_id=account_id,
            )
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
    items: list[EmailListItem] = []
    for email in emails:
        ext = ctx.extraction_repo.get_by_correlation_id(
            email.correlation_id,
            account_id=account_id,
        )
        review = ctx.review_repo.get(email.correlation_id, account_id=account_id)
        intent_val = effective_booking_intent(email, ext)
        intent_str = intent_val.value if intent_val else None
        items.append(
            EmailListItem(
                correlation_id=email.correlation_id,
                message_id=email.message_id,
                subject=email.subject,
                from_address=email.from_address,
                received_at=(
                    email.received_at.isoformat() if email.received_at else None
                ),
                platform=email.platform or (ext.platform if ext else None),
                intent=intent_str,
                booking_number=ext.booking_number if ext else None,
                processing_state=email.processing_state.value,
                review_status=review.review_status if review else None,
                grounding_flag=review.grounding_flag if review else False,
            )
        )
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
    )


def list_review_pending(
    ctx: AppContext,
    account_id: str,
    *,
    limit: int = 50,
) -> list[ReviewQueueItem]:
    items: list[ReviewQueueItem] = []
    for record in ctx.review_repo.list_pending(limit=200, account_id=account_id):
        email = ctx.email_repo.get_by_correlation_id(
            record.correlation_id,
            account_id=account_id,
        )
        if email is None:
            continue
        ext = ctx.extraction_repo.get_by_correlation_id(
            record.correlation_id,
            account_id=account_id,
        )
        if not classify_booking_mail(email, ext).is_booking:
            continue
        items.append(
            ReviewQueueItem(
                correlation_id=record.correlation_id,
                message_id=record.message_id,
                subject=email.subject,
                from_address=email.from_address,
                intent=record.intent,
                draft_body=record.draft_body,
                grounding_flag=record.grounding_flag,
                review_status=record.review_status,
                received_at=(
                    email.received_at.isoformat() if email.received_at else None
                ),
            )
        )
        if len(items) >= limit:
            break
    return items
