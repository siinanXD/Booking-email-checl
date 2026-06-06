"""Tests für IMAP SEARCH-Kriterien."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.infrastructure.adapters.mail.imap_search import build_imap_search_criterion


def test_build_imap_search_all() -> None:
    assert build_imap_search_criterion(unread_only=False, since=None) == ("ALL",)


def test_build_imap_search_unseen() -> None:
    assert build_imap_search_criterion(unread_only=True, since=None) == ("UNSEEN",)


def test_build_imap_search_since_and_unseen() -> None:
    since = datetime(2026, 6, 5, 12, 0, tzinfo=UTC)
    assert build_imap_search_criterion(unread_only=True, since=since) == (
        "UNSEEN",
        "SINCE",
        "05-Jun-2026",
    )
