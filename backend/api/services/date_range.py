"""Datumsbereich-Filter für Listen und KPIs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


def parse_date_range(
    *,
    from_date: str | None,
    to_date: str | None,
    default_days: int = 30,
) -> tuple[str, str]:
    """Liefert ISO-Grenzen (inklusive from, exklusive to+1 Tag)."""
    end = datetime.now(UTC)
    if to_date:
        end = _parse_iso(to_date)
    start = end - timedelta(days=default_days)
    if from_date:
        start = _parse_iso(from_date)
    if start > end:
        start, end = end, start
    return start.isoformat(), end.isoformat()


def _parse_iso(value: str) -> datetime:
    cleaned = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
