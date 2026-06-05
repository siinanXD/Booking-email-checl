"""Similarity-Search mit Mock-Embedding (nur Atlas, kein In-Memory)."""

from __future__ import annotations

from unittest.mock import patch

from backend.infrastructure.repositories.embedding_repository import EmbeddingRepository


class MockEmbedClient:
    """Test helper used by the suite."""

    def embed(self, text: str) -> list[float]:
        """Execute the operation."""
        return [1.0, 0.0] if "hello" in text else [0.0, 1.0]


def test_similar_cases_skipped_when_atlas_disabled(mock_db) -> None:
    """Ohne Atlas wird keine Suche ausgeführt – leere Liste, kein RAM-Scan."""
    from backend.ai.services.similarity_search import SimilaritySearchService

    repo = EmbeddingRepository(mock_db)
    repo.upsert_chunk("s1", "c1", "hello world", [1.0, 0.0], "guest_inquiry")
    svc = SimilaritySearchService(repo, MockEmbedClient(), use_atlas=False)
    results = svc.find_similar_cases("hello there", limit=1)
    assert results == []


def test_similar_cases_skips_embedding_call_when_disabled(mock_db) -> None:
    """Bei use_atlas=False darf nicht einmal embed() aufgerufen werden."""
    from backend.ai.services.similarity_search import SimilaritySearchService

    repo = EmbeddingRepository(mock_db)
    embed = MockEmbedClient()
    with patch.object(embed, "embed", wraps=embed.embed) as embed_spy:
        svc = SimilaritySearchService(repo, embed, use_atlas=False)
        svc.find_similar_cases("hello there", limit=1)
        embed_spy.assert_not_called()


def test_find_similar_cases_uses_atlas_when_enabled(mock_db) -> None:
    """Verify atlas backend is selected when use_atlas=True."""
    from backend.ai.services.similarity_search import SimilaritySearchService

    repo = EmbeddingRepository(mock_db)
    with patch.object(
        repo,
        "search_by_vector_atlas",
        return_value=[{"_id": "atlas-1"}],
    ) as atlas_mock:
        svc = SimilaritySearchService(repo, MockEmbedClient(), use_atlas=True)
        results = svc.find_similar_cases("hello there", limit=1)
        atlas_mock.assert_called_once()
        assert results[0]["_id"] == "atlas-1"


def test_atlas_offline_returns_empty(mock_db) -> None:
    """Atlas offline (OperationFailure) → leere Liste, kein Fallback-Scan."""
    from pymongo.errors import OperationFailure

    from backend.ai.services.similarity_search import SimilaritySearchService

    repo = EmbeddingRepository(mock_db)
    with patch.object(
        repo._col,
        "aggregate",
        side_effect=OperationFailure("vector index not found"),
    ):
        svc = SimilaritySearchService(repo, MockEmbedClient(), use_atlas=True)
        results = svc.find_similar_cases("hello there", limit=1)
        assert results == []
