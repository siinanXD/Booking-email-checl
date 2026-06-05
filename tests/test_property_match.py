"""Tests für Unterkunfts-Abgleich."""

from __future__ import annotations

from backend.ai.domain.booking.property_match import match_known_property_name


def test_match_known_property_substring() -> None:
    assert (
        match_known_property_name(
            "Unser Ferienhaus Nord bitte",
            ["Ferienhaus Nord"],
        )
        == "Ferienhaus Nord"
    )
