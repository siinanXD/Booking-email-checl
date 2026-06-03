"""Zähl- und Aggregations-Helfer für Buchungs-Mails."""

from __future__ import annotations

from datetime import datetime

from backend.ai.domain.booking.booking_relevance import (
    classify_booking_mail,
    effective_booking_intent,
)
from backend.core.models.email import StoredEmail
from backend.infrastructure.repositories.email_repository import EmailRepository
from backend.infrastructure.repositories.extraction_repository import (
    ExtractionRepository,
)


def count_booking_mails(
    email_repo: object,
    extraction_repo: object,
    *,
    since_iso: str | None = None,
    account_id: str | None = None,
) -> tuple[int, int, dict[str, int]]:
    """Zählt (gesamt, booking, nach Intent) optional seit received_at."""
    emails = email_repo if isinstance(email_repo, EmailRepository) else None
    extr = (
        extraction_repo if isinstance(extraction_repo, ExtractionRepository) else None
    )
    if emails is None or extr is None:
        return 0, 0, {}

    match: dict[str, object] = {}
    if since_iso:
        match["received_at"] = {"$gte": since_iso}
    if account_id:
        match["account_id"] = account_id
    total = 0
    booking = 0
    by_intent: dict[str, int] = {}
    for doc in emails._col.find(match):
        total += 1
        email = StoredEmail.from_mongo(doc)
        ext = extr.get_by_correlation_id(
            email.correlation_id,
            account_id=account_id,
        )
        verdict = classify_booking_mail(email, ext)
        if verdict.is_booking:
            booking += 1
            eff = effective_booking_intent(email, ext)
            key = eff.value if eff else "heuristic"
            by_intent[key] = by_intent.get(key, 0) + 1
    return total, booking, by_intent


def latest_booking_received_at(
    email_repo: object,
    extraction_repo: object,
    *,
    account_id: str | None = None,
) -> datetime | None:
    """Neuestes received_at einer als Buchung klassifizierten Mail."""
    emails = email_repo if isinstance(email_repo, EmailRepository) else None
    extr = (
        extraction_repo if isinstance(extraction_repo, ExtractionRepository) else None
    )
    if emails is None or extr is None:
        return None

    match: dict[str, object] = {}
    if account_id:
        match["account_id"] = account_id
    latest: datetime | None = None
    cursor = emails._col.find(match).sort("received_at", -1)
    for doc in cursor:
        email = StoredEmail.from_mongo(doc)
        ext = extr.get_by_correlation_id(
            email.correlation_id,
            account_id=account_id,
        )
        if not classify_booking_mail(email, ext).is_booking:
            continue
        received_at = email.received_at
        if received_at is None:
            continue
        if latest is None or received_at > latest:
            latest = received_at
    return latest
