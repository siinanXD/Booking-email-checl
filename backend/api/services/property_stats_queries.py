"""Unterkunfts-Historie aus Mails."""

from __future__ import annotations

from backend.ai.domain.booking.booking_relevance import classify_booking_mail
from backend.api.schemas.properties import PropertyHistoryItem, PropertyHistoryResponse
from backend.core.config.factory import AppContext
from backend.core.models.email import StoredEmail


def property_history(
    ctx: AppContext,
    account_id: str,
    *,
    property_name: str | None = None,
    limit: int = 50,
) -> PropertyHistoryResponse:
    items: list[PropertyHistoryItem] = []
    match: dict[str, object] = {"account_id": account_id}
    cursor = (
        ctx.email_repo._col.find(match)
        .sort("received_at", -1)
        .limit(min(max(limit * 3, 1), 500))
    )
    needle = (property_name or "").strip().lower()
    for doc in cursor:
        email = StoredEmail.from_mongo(doc)
        ext = ctx.extraction_repo.get_by_correlation_id(
            email.correlation_id,
            account_id=account_id,
        )
        if not classify_booking_mail(email, ext).is_booking:
            continue
        prop = (ext.property_name if ext else None) or ""
        if needle and prop.strip().lower() != needle:
            continue
        items.append(
            PropertyHistoryItem(
                correlation_id=email.correlation_id,
                subject=email.subject,
                received_at=(
                    email.received_at.isoformat() if email.received_at else None
                ),
                intent=ext.intent.value if ext and ext.intent else None,
                booking_number=ext.booking_number if ext else None,
                property_name=prop or None,
            )
        )
        if len(items) >= limit:
            break
    return PropertyHistoryResponse(items=items, total=len(items))
