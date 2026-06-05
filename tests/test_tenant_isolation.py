"""Mandanten-Isolation für Domänen-Collections."""

from __future__ import annotations

from datetime import UTC, date, datetime

from backend.ai.domain.booking.extraction import BookingExtraction
from backend.ai.services.entity_resolution import EntityResolutionService
from backend.ai.services.indexing import IndexingService
from backend.ai.services.similarity_search import SimilaritySearchService
from backend.core.models.email import StoredEmail
from backend.core.models.entities import Guest, Reservation
from backend.infrastructure.repositories.chunk_repository import ChunkRepository
from backend.infrastructure.repositories.embedding_repository import EmbeddingRepository


def test_guest_isolation_by_account(entity_repo) -> None:
    """Gast eines Mandanten ist für anderen Mandanten unsichtbar."""
    entity_repo.upsert_guest(
        Guest(guest_id="g-a", email="shared@test.com", name="Anna"),
        account_id="acc-a",
    )
    entity_repo.upsert_guest(
        Guest(guest_id="g-b", email="shared@test.com", name="Bob"),
        account_id="acc-b",
    )
    guest_a = entity_repo.get_guest_by_email("shared@test.com", account_id="acc-a")
    guest_b = entity_repo.get_guest_by_email("shared@test.com", account_id="acc-b")
    assert guest_a is not None
    assert guest_b is not None
    assert guest_a.guest_id == "g-a"
    assert guest_b.guest_id == "g-b"
    assert (
        entity_repo.get_guest_by_email("shared@test.com", account_id="acc-other")
        is None
    )


def test_booking_isolation_by_account(entity_repo) -> None:
    """Buchungsnummer ist pro Mandant getrennt."""
    entity_repo.upsert_guest(
        Guest(guest_id="g1", email="g@test.com"),
        account_id="acc-1",
    )
    entity_repo.upsert_reservation(
        Reservation(
            reservation_id="r1",
            guest_id="g1",
            booking_number="BN100",
            check_in=date(2026, 6, 1),
        ),
        account_id="acc-1",
    )
    assert entity_repo.find_reservation_by_booking_number("BN100", account_id="acc-1")
    assert (
        entity_repo.find_reservation_by_booking_number("BN100", account_id="acc-2")
        is None
    )


def test_entity_resolution_respects_account(entity_repo) -> None:
    """Entity Resolution matcht nur innerhalb des Mandanten."""
    entity_repo.upsert_guest(
        Guest(guest_id="g-x", email="guest@airbnb.com"),
        account_id="acc-x",
    )
    svc = EntityResolutionService(entity_repo)
    extraction = BookingExtraction(email="guest@airbnb.com")
    guest, _ = svc.resolve_guest(extraction, "other@example.com", account_id="acc-x")
    assert guest is not None
    guest_wrong, conf = svc.resolve_guest(
        extraction,
        "other@example.com",
        account_id="acc-y",
    )
    assert guest_wrong is None
    assert conf == 0.0


def test_embedding_search_atlas_filter_includes_account(mock_db) -> None:
    """Atlas $vectorSearch erhält den account_id-Filter (Tenant-Isolation)."""
    from unittest.mock import patch

    repo = EmbeddingRepository(mock_db)
    captured: dict[str, object] = {}

    def _fake_aggregate(pipeline: list[dict[str, object]]) -> list[dict[str, object]]:
        captured["pipeline"] = pipeline
        return [{"_id": "c-a"}]

    with patch.object(repo._col, "aggregate", side_effect=_fake_aggregate):
        results = repo.search_by_vector_atlas(
            [1.0, 0.0],
            limit=5,
            filter={"account_id": "acc-a"},
        )
    assert results[0]["_id"] == "c-a"
    stage = captured["pipeline"][0]["$vectorSearch"]  # type: ignore[index]
    assert stage["filter"] == {"account_id": "acc-a"}


def test_similarity_search_passes_account_filter(mock_db) -> None:
    """SimilaritySearchService reicht account_id an Atlas durch (use_atlas=True)."""
    from unittest.mock import patch

    class MockEmbed:
        def embed(self, text: str) -> list[float]:
            return [1.0, 0.0]

    repo = EmbeddingRepository(mock_db)
    with patch.object(
        repo, "search_by_vector_atlas", return_value=[{"_id": "s-a"}]
    ) as atlas_mock:
        svc = SimilaritySearchService(repo, MockEmbed(), use_atlas=True)
        results = svc.find_similar_cases("hello", limit=5, account_id="acc-a")
    assert results[0]["_id"] == "s-a"
    # account_id muss im Filter an Atlas weitergereicht werden
    _, kwargs = atlas_mock.call_args
    assert kwargs["filter"] == {"account_id": "acc-a"}


def test_indexing_writes_chunks_with_account(mock_db) -> None:
    """Indexierung speichert Chunks und Embeddings mit account_id."""
    import asyncio

    class MockEmbed:
        def embed(self, text: str) -> list[float]:
            return [1.0, 0.0]

    emb_repo = EmbeddingRepository(mock_db)
    chunk_repo = ChunkRepository(mock_db)
    svc = IndexingService(emb_repo, MockEmbed(), chunk_repo)
    asyncio.run(svc._index_async("corr-idx", "Hello\n\nWorld", None, "acc-idx"))
    chunk_doc = chunk_repo._col.find_one({"_id": "corr-idx:0"})
    emb_doc = emb_repo._col.find_one({"_id": "corr-idx:0"})
    assert chunk_doc is not None
    assert emb_doc is not None
    assert chunk_doc["account_id"] == "acc-idx"
    assert emb_doc["account_id"] == "acc-idx"


def test_retrieval_scoped_by_account(entity_repo, email_repo) -> None:
    """Retrieval lädt nur Buchungen des Mail-Mandanten."""
    from backend.ai.services.retrieval import RetrievalService

    entity_repo.upsert_guest(
        Guest(guest_id="g1", email="x@test.com"),
        account_id="acc-1",
    )
    entity_repo.upsert_reservation(
        Reservation(reservation_id="r1", guest_id="g1", booking_number="B1"),
        account_id="acc-1",
    )
    entity_repo.upsert_guest(
        Guest(guest_id="g2", email="x@test.com"),
        account_id="acc-2",
    )
    entity_repo.upsert_reservation(
        Reservation(reservation_id="r2", guest_id="g2", booking_number="B2"),
        account_id="acc-2",
    )
    email = StoredEmail(
        message_id="m-tenant",
        from_address="x@test.com",
        body_text="Hi",
        received_at=datetime.now(UTC),
        account_id="acc-1",
    )
    email_repo.upsert_by_message_id(email)
    hits = RetrievalService(entity_repo, email_repo).retrieve(
        email,
        BookingExtraction(email="x@test.com"),
    )
    assert hits.guest is not None
    assert hits.guest.guest_id == "g1"
    assert len(hits.reservations) == 1
    assert hits.reservations[0].booking_number == "B1"
