"""WhatsApp-Template-Auswahl und Parameter."""

from __future__ import annotations

import re
from datetime import date

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.core.config.settings import Settings
from backend.core.models.notification import NotificationKind

_E164_RE = re.compile(r"^\+[1-9]\d{6,14}$")


def kind_for_extraction(extraction: BookingExtraction) -> NotificationKind | None:
    intent = extraction.intent
    if intent in (BookingIntent.NEW_BOOKING, None):
        return NotificationKind.BOOKING_CLEANING_TASK
    if intent in (
        BookingIntent.CHANGE,
        BookingIntent.CANCELLATION,
        BookingIntent.PAYMENT_ISSUE,
    ):
        return NotificationKind.BOOKING_STATUS_NOTICE
    if intent in (BookingIntent.GUEST_INQUIRY, BookingIntent.COMPLAINT):
        return NotificationKind.BOOKING_GUEST_INQUIRY
    return None


def build_template_payload(
    kind: NotificationKind,
    extraction: BookingExtraction,
    settings: Settings,
) -> tuple[str, list[str]]:
    if kind == NotificationKind.BOOKING_CLEANING_TASK:
        return settings.whatsapp_template_cleaning_task, [
            _text(extraction.property_name, "Unbekannte Unterkunft"),
            _format_date(extraction.check_in),
            _format_date(extraction.check_out),
            _cleaning_label(extraction),
            _text(extraction.booking_number, "—"),
        ]
    if kind == NotificationKind.BOOKING_GUEST_INQUIRY:
        return settings.whatsapp_template_guest_inquiry, [
            _inquiry_label(extraction),
            _text(extraction.property_name, "Unbekannte Unterkunft"),
            _text(extraction.booking_number, "—"),
            _format_date(extraction.check_in),
            _format_date(extraction.check_out),
            _text(extraction.guest_name, "—"),
        ]
    return settings.whatsapp_template_status_notice, [
        _status_label(extraction),
        _text(extraction.property_name, "Unbekannte Unterkunft"),
        _format_date(extraction.check_in),
        _format_date(extraction.check_out),
        _text(extraction.guest_name, "—"),
        _text(extraction.booking_number, "—"),
    ]


def parse_recipient_list(raw: str) -> list[str]:
    if not raw.strip():
        return []
    result: list[str] = []
    for part in raw.split(","):
        phone = part.strip()
        if phone and _E164_RE.match(phone):
            result.append(phone)
    return result


def _text(value: str | None, fallback: str) -> str:
    if value and value.strip():
        return value.strip()
    return fallback


def _format_date(value: date | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d.%m.%Y")


def _cleaning_label(extraction: BookingExtraction) -> str:
    if extraction.intent == BookingIntent.NEW_BOOKING:
        return "Check-out Reinigung"
    return _text(extraction.status, "Reinigung")


def _status_label(extraction: BookingExtraction) -> str:
    if extraction.intent == BookingIntent.CANCELLATION:
        return "Storno"
    if extraction.intent == BookingIntent.CHANGE:
        return "Änderung"
    if extraction.intent == BookingIntent.PAYMENT_ISSUE:
        return "Zahlungsproblem"
    return _text(extraction.status, "Update")


def _inquiry_label(extraction: BookingExtraction) -> str:
    if extraction.intent == BookingIntent.COMPLAINT:
        return "Beschwerde"
    return "Gastnachricht"
