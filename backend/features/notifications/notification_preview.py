"""WhatsApp-Vorschau ohne Versand."""

from __future__ import annotations

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.api.schemas.review_whatsapp import (
    WhatsAppPreviewMessage,
    WhatsAppPreviewResponse,
)
from backend.core.config.factory import AppContext
from backend.features.notifications.notification_template_payload import (
    build_template_payload,
    kind_for_extraction,
    parse_recipient_list,
)
from backend.features.platform.effective_settings import merge_platform_settings
from backend.infrastructure.repositories.property_recipient_repository import (
    PropertyRecipientRepository,
)


def build_whatsapp_preview(
    ctx: AppContext,
    account_id: str,
    correlation_id: str,
    extraction: BookingExtraction,
) -> WhatsAppPreviewResponse:
    """Baut Template-Vorschau für alle konfigurierten Empfänger."""
    platform = ctx.platform_settings_repo.get(account_id)
    settings = merge_platform_settings(ctx.settings, platform)
    if not settings.whatsapp_enabled:
        return WhatsAppPreviewResponse(
            correlation_id=correlation_id,
            enabled=False,
            note="WhatsApp ist deaktiviert.",
        )
    kind = kind_for_extraction(extraction)
    if kind is None:
        return WhatsAppPreviewResponse(
            correlation_id=correlation_id,
            enabled=True,
            note="Kein Template für diesen Intent.",
        )
    template_name, params = build_template_payload(kind, extraction, settings)
    recipients = _preview_recipients(
        ctx.property_recipient_repo,
        ctx.user_repo.list_whatsapp_recipient_phones(account_id),
        settings.whatsapp_default_recipients,
        extraction,
        account_id=account_id,
    )
    if not recipients:
        return WhatsAppPreviewResponse(
            correlation_id=correlation_id,
            enabled=True,
            note="Keine Empfänger konfiguriert.",
        )
    messages = [
        WhatsAppPreviewMessage(
            recipient_e164=phone,
            template_name=template_name,
            template_language=settings.whatsapp_template_language,
            template_params=params,
            kind=kind.value,
        )
        for phone in recipients
    ]
    return WhatsAppPreviewResponse(
        correlation_id=correlation_id,
        enabled=True,
        messages=messages,
    )


def _preview_recipients(
    property_repo: PropertyRecipientRepository,
    user_phones: list[str],
    default_raw: str,
    extraction: BookingExtraction,
    *,
    account_id: str,
) -> list[str]:
    from backend.ai.domain.booking.taxonomy import BookingIntent

    phones: set[str] = set(user_phones)
    phones.update(parse_recipient_list(default_raw))
    intent = extraction.intent
    if intent in (BookingIntent.NEW_BOOKING, None):
        phones.update(
            property_repo.get_phones(
                extraction.property_name,
                account_id=account_id,
            )
        )
    return sorted(phones)
