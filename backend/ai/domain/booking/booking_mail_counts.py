"""Zähl- und Aggregations-Helfer für Buchungs-Mails."""

from __future__ import annotations

from dataclasses import dataclass, field
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

# Für Klassifikation reicht ein Prefix; spart Atlas-Transfer bei großen Mails.
_BODY_PREFIX_CHARS = 4000
_BOOKING_COUNT_PROJECTION: dict[str, object] = {
    "_id": 1,
    "correlation_id": 1,
    "message_id": 1,
    "from_address": 1,
    "subject": 1,
    "platform": 1,
    "received_at": 1,
    "account_id": 1,
    "processing_state": 1,
    "triage_outcome": 1,
    "body_text": {"$substrCP": ["$body_text", 0, _BODY_PREFIX_CHARS]},
}


def _load_emails_for_count(
    emails: EmailRepository,
    match: dict[str, object],
) -> list[StoredEmail]:
    """Lädt Mails mit schlanker Projektion für Zähl-Queries."""
    pipeline: list[dict[str, object]] = []
    if match:
        pipeline.append({"$match": match})
    pipeline.append({"$project": _BOOKING_COUNT_PROJECTION})
    return [StoredEmail.from_mongo(doc) for doc in emails._col.aggregate(pipeline)]


@dataclass
class BookingMailStats:
    """Aggregierte Buchungs-KPIs aus einem Durchlauf."""

    booking_total: int = 0
    booking_week: int = 0
    intents_today: dict[str, int] = field(default_factory=dict)
    intents_all: dict[str, int] = field(default_factory=dict)
    latest_booking_received_at: datetime | None = None


def aggregate_booking_mail_stats(
    email_repo: object,
    extraction_repo: object,
    *,
    account_id: str | None,
    today_iso: str,
    week_iso: str,
) -> BookingMailStats:
    """Einzelner Scan: alle KPIs + letzte Buchungs-Mail."""
    emails = email_repo if isinstance(email_repo, EmailRepository) else None
    extr = (
        extraction_repo if isinstance(extraction_repo, ExtractionRepository) else None
    )
    if emails is None or extr is None:
        return BookingMailStats()

    match: dict[str, object] = {}
    if account_id:
        match["account_id"] = account_id

    email_docs = _load_emails_for_count(emails, match)
    if not email_docs:
        return BookingMailStats()

    parsed: list[StoredEmail] = email_docs
    correlation_ids = [e.correlation_id for e in parsed]
    extractions = extr.map_by_correlation_ids(correlation_ids, account_id=account_id)

    stats = BookingMailStats()
    for email in parsed:
        ext = extractions.get(email.correlation_id)
        verdict = classify_booking_mail(email, ext)
        if not verdict.is_booking:
            continue

        stats.booking_total += 1
        received_at = email.received_at
        received_iso = received_at.isoformat() if received_at else None
        if received_iso and received_iso >= week_iso:
            stats.booking_week += 1

        eff = effective_booking_intent(email, ext)
        key = eff.value if eff else "heuristic"
        stats.intents_all[key] = stats.intents_all.get(key, 0) + 1
        if received_iso and received_iso >= today_iso:
            stats.intents_today[key] = stats.intents_today.get(key, 0) + 1

        if received_at is None:
            continue
        if (
            stats.latest_booking_received_at is None
            or received_at > stats.latest_booking_received_at
        ):
            stats.latest_booking_received_at = received_at

    return stats


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

    email_docs = _load_emails_for_count(emails, match)
    if not email_docs:
        return 0, 0, {}

    parsed = email_docs
    extractions = extr.map_by_correlation_ids(
        [e.correlation_id for e in parsed],
        account_id=account_id,
    )

    total = len(parsed)
    booking = 0
    by_intent: dict[str, int] = {}
    for email in parsed:
        ext = extractions.get(email.correlation_id)
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
    stats = aggregate_booking_mail_stats(
        email_repo,
        extraction_repo,
        account_id=account_id,
        today_iso="1970-01-01T00:00:00+00:00",
        week_iso="1970-01-01T00:00:00+00:00",
    )
    return stats.latest_booking_received_at
