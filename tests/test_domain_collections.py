"""Unit-Tests für MongoDB-Domänen-Collections."""

from __future__ import annotations

import mongomock

from backend.infrastructure.repositories.domain_collections import (
    BOOKINGS,
    CHUNKS,
    CONVERSATIONS,
    DOMAIN_COLLECTIONS,
    EMAILS,
    EMBEDDINGS,
    GUESTS,
    PROPERTIES,
    ensure_domain_collections,
)


def test_ensure_domain_collections_creates_all() -> None:
    """Fehlende Collections werden beim Bootstrap angelegt."""
    client: mongomock.MongoClient = mongomock.MongoClient()
    db = client["test_db"]
    ensure_domain_collections(db)
    assert set(db.list_collection_names()) == set(DOMAIN_COLLECTIONS)


def test_ensure_domain_collections_idempotent() -> None:
    """Zweiter Aufruf erzeugt keine Duplikate."""
    client: mongomock.MongoClient = mongomock.MongoClient()
    db = client["test_db"]
    db.create_collection(EMAILS)
    db[EMAILS].insert_one({"_id": "m1", "subject": "Hi"})
    ensure_domain_collections(db)
    ensure_domain_collections(db)
    assert set(db.list_collection_names()) == set(DOMAIN_COLLECTIONS)
    assert db[EMAILS].count_documents({}) == 1


def test_migrate_reservations_to_bookings() -> None:
    """Legacy-Collection `reservations` wird in `bookings` umbenannt."""
    client: mongomock.MongoClient = mongomock.MongoClient()
    db = client["test_db"]
    db.create_collection("reservations")
    db["reservations"].insert_one({"_id": "r1", "booking_number": "AB100"})
    ensure_domain_collections(db)
    assert "reservations" not in db.list_collection_names()
    assert BOOKINGS in db.list_collection_names()
    assert db[BOOKINGS].count_documents({}) == 1
    for name in (GUESTS, PROPERTIES, CONVERSATIONS, CHUNKS, EMBEDDINGS):
        assert name in db.list_collection_names()
