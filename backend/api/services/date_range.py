"""Datumsbereich-Filter für Listen und KPIs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


def parse_date_range(
    *,
    from_date: str | None,
    to_date: str | None,
    default_days: int = 30,
) -> tuple[str, str]:
    """Liefert ISO-Grenzen (inklusive from und to, jeweils ganzer Kalendertag)."""
    end = datetime.now(UTC)
    if to_date:
        end = (
            _end_of_day(_parse_iso(to_date))
            if _is_date_only(to_date)
            else _parse_iso(to_date)
        )
    start = end - timedelta(days=default_days)
    if from_date:
        parsed_from = _parse_iso(from_date)
        start = _start_of_day(parsed_from) if _is_date_only(from_date) else parsed_from
    if start > end:
        start, end = end, start
    return start.isoformat(), end.isoformat()


def _is_date_only(value: str) -> bool:
    cleaned = value.strip()
    return len(cleaned) == 10 and cleaned[4] == "-" and cleaned[7] == "-"


def _start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _end_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def _parse_iso(value: str) -> datetime:
    cleaned = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
