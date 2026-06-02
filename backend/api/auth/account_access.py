"""Account-Zugriffsprüfungen für Auth."""

from __future__ import annotations

from backend.infrastructure.repositories.account_repository import (
    AccountRecord,
    AccountRepository,
)
from backend.infrastructure.repositories.user_repository import UserRecord


def account_login_error(account: AccountRecord | None) -> str | None:
    """Liefert Fehlermeldung wenn Login wegen Account-Status blockiert ist."""
    if account is None:
        return None
    if account.status == "pending":
        return (
            "Dein Konto wartet auf Freischaltung. "
            "Du erhältst eine E-Mail, sobald es freigegeben wurde."
        )
    if account.status == "rejected":
        reason = (account.rejection_reason or "").strip()
        if reason:
            return f"Registrierung abgelehnt: {reason}"
        return "Deine Registrierung wurde abgelehnt."
    if account.status == "suspended":
        return "Dein Konto wurde vorübergehend gesperrt."
    return None


def load_user_account(
    user: UserRecord,
    account_repo: AccountRepository,
) -> AccountRecord | None:
    """Lädt den Account eines Benutzers."""
    if not user.account_id:
        return None
    return account_repo.get_by_id(user.account_id)
