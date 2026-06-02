"""PII-Maskierung."""

from __future__ import annotations

from backend.core.utils.pii import mask_pii


def test_mask_email_and_phone() -> None:
    """Verify mask email and phone."""
    text = "Kontakt: user@example.com oder +49 170 1234567"
    masked = mask_pii(text)
    assert "user@example.com" not in masked
    assert "[EMAIL]" in masked
