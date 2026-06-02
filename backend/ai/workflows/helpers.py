"""Shared helpers for email workflow execution."""

from __future__ import annotations

from typing import Any

from backend.core.models.email import IncomingEmail, StoredEmail
from backend.infrastructure.observability.mail_cost import MailCostTracker


def account_id_from_email(
    email_input: Any,
    result: dict[str, Any] | None,
) -> str | None:
    if result is not None:
        email = result.get("email")
        if isinstance(email, StoredEmail):
            return email.account_id
    if isinstance(email_input, IncomingEmail | StoredEmail):
        return email_input.account_id
    return None


def correlation_id(email_input: Any, result: dict[str, Any] | None) -> str | None:
    if result is not None:
        email = result.get("email")
        if isinstance(email, StoredEmail):
            return email.correlation_id
    if isinstance(email_input, IncomingEmail | StoredEmail):
        return email_input.correlation_id
    return None


def finalize_mail_cost(
    mail_cost: MailCostTracker | None,
    email_input: Any,
    result: dict[str, Any] | None,
) -> None:
    if mail_cost is None:
        return
    cid = correlation_id(email_input, result)
    if cid:
        mail_cost.finalize(
            cid,
            account_id=account_id_from_email(email_input, result),
        )
