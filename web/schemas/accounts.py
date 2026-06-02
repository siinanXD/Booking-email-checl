"""Account-Admin-DTOs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AccountListItem(BaseModel):
    """Account-Metadaten für Admin-Listen."""

    id: str
    display_name: str
    contact_email: str
    account_type: str
    company_name: str | None = None
    phone: str | None = None
    status: str
    rejection_reason: str | None = None
    created_at: str


class AccountListResponse(BaseModel):
    """Liste von Accounts."""

    items: list[AccountListItem]
    total: int


class AccountRejectRequest(BaseModel):
    """Optionaler Ablehnungsgrund."""

    reason: str | None = Field(default=None, max_length=500)


class AccountActionResponse(BaseModel):
    """Ergebnis Freischalten/Ablehnen."""

    id: str
    status: str
    message: str
