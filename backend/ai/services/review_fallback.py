"""Fallback-Entwurf wenn LLM oder Template fehlen."""

from __future__ import annotations

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.domain.booking.taxonomy import BookingIntent
from backend.core.models.email import StoredEmail


def fallback_draft_body(
    email: StoredEmail,
    extraction: BookingExtraction,
) -> str:
    """Kurzer manueller Entwurf als Fallback."""
    guest = (extraction.guest_name or "Gast").strip()
    booking = extraction.booking_number or "—"
    intent = extraction.intent or BookingIntent.GUEST_INQUIRY
    if intent == BookingIntent.CANCELLATION:
        opener = (
            f"Guten Tag {guest},\n\nwir haben Ihre Stornierung ({booking}) erhalten."
        )
    elif intent == BookingIntent.NEW_BOOKING:
        opener = f"Guten Tag {guest},\n\nvielen Dank für Ihre Buchung ({booking})."
    else:
        opener = f"Guten Tag {guest},\n\nvielen Dank für Ihre Nachricht ({booking})."
    return (
        f"{opener}\n\n"
        f"Betreff: {email.subject}\n\n"
        "Bitte prüfen und bei Bedarf anpassen.\n\n"
        "Freundliche Grüße"
    )
