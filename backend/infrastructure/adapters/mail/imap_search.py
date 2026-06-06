"""IMAP SEARCH-Kriterien für Mail-Polling."""

from __future__ import annotations

from datetime import datetime

from backend.infrastructure.adapters.outlook.poll_window import format_imap_since_date


def build_imap_search_criterion(
    *,
    unread_only: bool,
    since: datetime | None,
) -> tuple[str, ...]:
    """Suchkriterien für ``IMAP4.search`` (neueste Mails im Zeitfenster)."""
    parts: list[str] = []
    if unread_only:
        parts.append("UNSEEN")
    if since is not None:
        parts.append("SINCE")
        parts.append(format_imap_since_date(since))
    if not parts:
        return ("ALL",)
    return tuple(parts)
