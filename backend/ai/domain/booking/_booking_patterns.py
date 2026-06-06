"""Regex-Muster und Hilfsfunktionen für Buchungs-Mail-Erkennung."""

from __future__ import annotations

import re

from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.core.models.email import IncomingEmail, StoredEmail

EmailLike = IncomingEmail | StoredEmail

# --- Absender / Betreff: klar KEINE Buchungsmail ---
_NOISE_SENDER_SUBSTRINGS = (
    "comigo",
    "lumigita",
    "lomigata",
    "newsletter",
    "mailchimp",
    "sendgrid.net",
    "constantcontact",
    "linkedin.com",
    "github.com",
    "temu.com",
    "amazon.",
    "haystack",
    "indeed.",
    "xing.com",
    "stepstone",
    "nvidia.com",
    "microsoft.com",
    "notifications@",
    "noreply@notify",
)

_NON_BOOKING_SUBJECT_RE = re.compile(
    r"(prime\s*day|temu|linkedin|github|run\s+failed|ci\s*-|codex|haystack|"
    r"software\s+engineer|kontaktanfrage|cv\s+und|bestellung\s+wurde|"
    r"zugriffstoken|widerrufen|elektroingenieur|standpunkt|belohnung|"
    r"ankünfte\s+in\s+möbeln|maintanace|emoji|temu-bellet)",
    re.IGNORECASE,
)

_NOISE_SUBJECT_PATTERNS = (
    re.compile(r"\bcomigo\b", re.IGNORECASE),
    re.compile(r"\blumigita\b", re.IGNORECASE),
    re.compile(r"\bnewsletter\b", re.IGNORECASE),
    re.compile(r"\bwerbung\b", re.IGNORECASE),
    re.compile(r"\bunsubscribe\b", re.IGNORECASE),
)

# Beds24 / PMS — starke Indikatoren
_BEDS24_SUBJECT_RE = re.compile(
    r"^(Buchung|Stornierung|Buchungsänderung|Nachricht vom Gast)\s*:",
    re.IGNORECASE,
)

_BOOKING_SIGNAL_RE = re.compile(
    r"(buchung|booking|reservierung|storno|stornierung|cancel|"
    r"beds24|airbnb|booking\.com|vrbo|expedia|münzbach|muenzbach|"
    r"ferienzimmer|zimmer\s+nr|gäste|guest|anreise|abreise|übernacht)",
    re.IGNORECASE,
)

# Gast-Anfrage ohne PMS-Betreff (z. B. „ich möchte buchen")
_RESERVATION_REQUEST_RE = re.compile(
    r"(möchte\s+(gerne\s+)?(eine\s+)?buchung|würde\s+gerne\s+.*buchung|"
    r"buchung\s+tätigen|zimmer\s+reservieren|reservierung\s+anfragen|"
    r"would\s+like\s+to\s+(make\s+a\s+)?book|like\s+to\s+book|"
    r"book\s+a\s+room|make\s+a\s+reservation|availability|verfügbarkeit)",
    re.IGNORECASE,
)

_TRUSTED_BOOKING_DOMAINS = (
    "beds24.com",
    "beds24.de",
    "airbnb.com",
    "booking.com",
    "guest.booking.com",
    "expedia.com",
    "vrbo.com",
)

# LLM erfindet oft AB200 / XY999 bei Werbe-Mails
_FAKE_BOOKING_NUMBER_RE = re.compile(r"^[A-Z]{2}\d{2,4}$", re.IGNORECASE)

_BOOKING_INTENTS = frozenset(
    {
        BookingIntent.NEW_BOOKING,
        BookingIntent.CHANGE,
        BookingIntent.CANCELLATION,
        BookingIntent.GUEST_INQUIRY,
    }
)


def _from_domain(from_address: str) -> str:
    if "@" not in from_address:
        return ""
    return from_address.split("@")[-1].lower().strip()


def is_trusted_booking_domain(from_address: str) -> bool:
    """Absender-Domain gehört zu bekannten Buchungs-/PMS-Plattformen."""
    domain = _from_domain(from_address)
    return bool(domain) and any(known in domain for known in _TRUSTED_BOOKING_DOMAINS)


def has_text_booking_signals(email: EmailLike) -> bool:
    """Buchungs-Keywords in Betreff oder Body (ohne Extraktion)."""
    combined = f"{email.subject or ''}\n{email.body_text or ''}"
    return bool(_BOOKING_SIGNAL_RE.search(combined))


def has_reservation_request_signals(email: EmailLike) -> bool:
    """Freitext-Anfrage nach neuer Buchung / Reservierung."""
    combined = f"{email.subject or ''}\n{email.body_text or ''}"
    return bool(_RESERVATION_REQUEST_RE.search(combined))


def is_marketing_noise(email: EmailLike) -> bool:
    """Newsletter / interne Infos."""
    from_addr = (email.from_address or "").lower()
    subject = email.subject or ""
    for frag in _NOISE_SENDER_SUBSTRINGS:
        if frag in from_addr:
            return True
    for pattern in _NOISE_SUBJECT_PATTERNS:
        if pattern.search(subject):
            return True
    return False
