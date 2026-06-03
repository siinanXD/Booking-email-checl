"""Domänen-Collections für MongoDB Atlas (Bootstrap beim Connect)."""

from __future__ import annotations

import logging

from pymongo.errors import CollectionInvalid

from backend.infrastructure.repositories.mongo import Db

logger = logging.getLogger(__name__)

EMAILS = "emails"
BOOKINGS = "bookings"
GUESTS = "guests"
PROPERTIES = "properties"
CONVERSATIONS = "conversations"
CHUNKS = "chunks"
EMBEDDINGS = "embeddings"

DOMAIN_COLLECTIONS: tuple[str, ...] = (
    EMAILS,
    BOOKINGS,
    GUESTS,
    PROPERTIES,
    CONVERSATIONS,
    CHUNKS,
    EMBEDDINGS,
)

_LEGACY_RESERVATIONS = "reservations"


def ensure_domain_collections(db: Db) -> None:
    """Legt fehlende Domänen-Collections an (idempotent, Atlas-kompatibel)."""
    existing = set(db.list_collection_names())
    _migrate_reservations_to_bookings(db, existing)
    existing = set(db.list_collection_names())
    for name in DOMAIN_COLLECTIONS:
        if name in existing:
            continue
        try:
            db.create_collection(name)
            logger.info("MongoDB collection created: %s", name)
        except CollectionInvalid:
            logger.debug("MongoDB collection already exists: %s", name)
        existing.add(name)


def _migrate_reservations_to_bookings(db: Db, existing: set[str]) -> None:
    """Benennt legacy `reservations` in `bookings` um, falls nötig."""
    if _LEGACY_RESERVATIONS not in existing or BOOKINGS in existing:
        return
    db[_LEGACY_RESERVATIONS].rename(BOOKINGS)
    logger.info(
        "MongoDB collection renamed: %s -> %s",
        _LEGACY_RESERVATIONS,
        BOOKINGS,
    )
