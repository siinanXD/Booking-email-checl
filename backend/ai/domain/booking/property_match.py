"""Abgleich extrahierter Unterkunftsnamen mit dem Mandanten-Katalog."""

from __future__ import annotations


def match_known_property_name(
    candidate: str | None,
    known_names: list[str],
) -> str | None:
    """Findet den passenden Katalog-Namen (case-insensitive, Teilstring)."""
    raw = (candidate or "").strip()
    if not raw or not known_names:
        return None
    low = raw.lower()
    for name in known_names:
        key = name.strip().lower()
        if not key:
            continue
        if low == key or key in low or low in key:
            return name
    return None
