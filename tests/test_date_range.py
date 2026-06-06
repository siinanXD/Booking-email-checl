"""Tests für date_range."""

from __future__ import annotations

from backend.api.services.date_range import parse_date_range


def test_parse_with_explicit_dates() -> None:
    start, end = parse_date_range(
        from_date="2026-01-01",
        to_date="2026-01-31",
        default_days=7,
    )
    assert start.startswith("2026-01-01T00:00:00")
    assert end.startswith("2026-01-31T23:59:59")


def test_to_date_includes_emails_received_later_same_day() -> None:
    _, end = parse_date_range(
        from_date="2026-06-06",
        to_date="2026-06-06",
        default_days=7,
    )
    assert end >= "2026-06-06T13:31:00+00:00"
