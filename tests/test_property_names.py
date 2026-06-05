"""Tests für tenant_properties."""

from __future__ import annotations

from types import SimpleNamespace

from backend.api.services.tenant_properties import list_property_names
from backend.infrastructure.repositories.property_recipient_repository import (
    PropertyRecipientRepository,
)
from backend.infrastructure.repositories.property_repository import PropertyRepository


def test_list_property_names_from_recipients(mock_db: object) -> None:
    repo = PropertyRecipientRepository(mock_db)  # type: ignore[arg-type]
    repo.upsert("acc-t", "Alpine Chalet", ["+491701111111"])
    ctx = SimpleNamespace(
        db=mock_db,
        property_recipient_repo=repo,
    )
    names = list_property_names(ctx, "acc-t")  # type: ignore[arg-type]
    assert "Alpine Chalet" in names
    assert PropertyRepository(mock_db).list_all(account_id="acc-t") == []  # type: ignore[arg-type]
