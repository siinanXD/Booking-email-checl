"""Tests für date_range."""

from __future__ import annotations

from backend.api.services.date_range import parse_date_range


def test_parse_with_explicit_dates() -> None:
    start, end = parse_date_range(
        from_date="2026-01-01",
        to_date="2026-01-31",
        default_days=7,
    )
    assert start.startswith("2026-01-01")
    assert "2026-01-31" in end
