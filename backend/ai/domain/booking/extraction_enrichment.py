"""Anreicherung von Extraktionen vor Review/Display."""

from __future__ import annotations

import re

from backend.ai.domain.booking.booking_relevance import has_reservation_request_signals
from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.property_match import match_known_property_name
from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.core.models.email import StoredEmail

_GUEST_PLACEHOLDERS = frozenset(
    {"gast", "guest", "unbekannt", "unknown", "n/a", "—", "-"}
)

_EMAIL_IN_BODY_RE = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
)


def enrich_extraction(
    email: StoredEmail,
    extraction: BookingExtraction,
    *,
    known_property_names: list[str] | None = None,
) -> BookingExtraction:
    """Ergänzt fehlende Felder heuristisch aus Mail-Metadaten."""
    data = extraction.model_dump()
    if not data.get("platform") and email.platform:
        data["platform"] = email.platform
    guest = (data.get("guest_name") or "").strip()
    if not guest or guest.lower() in _GUEST_PLACEHOLDERS:
        inferred = _guest_from_subject(email.subject) or _guest_from_body(
            email.body_text or ""
        )
        if inferred:
            data["guest_name"] = inferred
    if not data.get("email"):
        from_addr = (email.from_address or "").strip()
        if "@" in from_addr and not from_addr.lower().startswith("noreply"):
            data["email"] = from_addr
        else:
            body_mail = _email_from_body(email.body_text or "")
            if body_mail:
                data["email"] = body_mail
    intent_raw = data.get("intent")
    intent_key = (
        intent_raw.value
        if isinstance(intent_raw, BookingIntent)
        else str(intent_raw or "")
    )
    if has_reservation_request_signals(email) and intent_key in (
        "",
        BookingIntent.OTHER.value,
        BookingIntent.GUEST_INQUIRY.value,
    ):
        data["intent"] = BookingIntent.NEW_BOOKING
    if data.get("intent") is None:
        data["intent"] = BookingIntent.GUEST_INQUIRY
    if known_property_names:
        matched = match_known_property_name(
            data.get("property_name"),
            known_property_names,
        )
        if matched:
            data["property_name"] = matched
    return BookingExtraction.model_validate(data)


def _guest_from_subject(subject: str) -> str | None:
    if " - " not in subject:
        return None
    tail = subject.split(" - ", 1)[-1].strip()
    if len(tail) < 2 or len(tail) > 80:
        return None
    if any(ch.isdigit() for ch in tail[:6]):
        return None
    return tail


def _guest_from_body(body: str) -> str | None:
    for line in body.splitlines():
        text = line.strip()
        if not text:
            continue
        m = re.match(
            r"^(?:name|gast|guest)\s*[:]\s*(.+)$",
            text,
            re.IGNORECASE,
        )
        if m:
            name = m.group(1).strip()
            if 2 <= len(name) <= 80:
                return name
    return None


def _email_from_body(body: str) -> str | None:
    match = _EMAIL_IN_BODY_RE.search(body)
    if match is None:
        return None
    return match.group(0).strip().lower()
