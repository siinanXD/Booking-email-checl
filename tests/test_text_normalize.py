"""Body-Normalisierung inkl. HTML-Fallback."""

from __future__ import annotations

from backend.core.utils.text import normalize_body


def test_normalize_body_from_html() -> None:
    """Verify normalize body from html."""
    html = "<p>Hallo</p><p>Welt</p>"
    text = normalize_body("", html)
    assert "Hallo" in text
    assert "<p>" not in text
