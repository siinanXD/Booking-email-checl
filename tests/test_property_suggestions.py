"""Tests für property_suggestions_queries."""

from __future__ import annotations

from types import SimpleNamespace

from backend.api.services.property_suggestions_queries import property_suggestions
from backend.infrastructure.repositories.email_repository import EmailRepository
from backend.infrastructure.repositories.extraction_repository import (
    ExtractionRepository,
)
from backend.infrastructure.repositories.property_recipient_repository import (
    PropertyRecipientRepository,
)


def test_suggestions_returns_list(mock_db: object) -> None:
    ctx = SimpleNamespace(
        db=mock_db,
        email_repo=EmailRepository(mock_db),  # type: ignore[arg-type]
        extraction_repo=ExtractionRepository(mock_db),  # type: ignore[arg-type]
        property_recipient_repo=PropertyRecipientRepository(mock_db),  # type: ignore[arg-type]
    )
    result = property_suggestions(ctx, "acc-empty", limit=5)  # type: ignore[arg-type]
    assert result.items == []
