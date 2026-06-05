"""Properties-API-Schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.infrastructure.repositories.property_recipient_repository import (
    PropertyWhatsAppRecipients,
)


class PropertyRecipientsResponse(BaseModel):
    items: list[PropertyWhatsAppRecipients] = Field(default_factory=list)


class PropertyRecipientsUpdateRequest(BaseModel):
    items: list[PropertyWhatsAppRecipients] = Field(default_factory=list)


class PropertyHistoryItem(BaseModel):
    correlation_id: str
    subject: str = ""
    received_at: str | None = None
    intent: str | None = None
    booking_number: str | None = None
    property_name: str | None = None


class PropertyHistoryResponse(BaseModel):
    items: list[PropertyHistoryItem] = Field(default_factory=list)
    total: int = 0


class PropertySuggestion(BaseModel):
    property_name: str
    mail_count: int = 0


class PropertySuggestionsResponse(BaseModel):
    items: list[PropertySuggestion] = Field(default_factory=list)
