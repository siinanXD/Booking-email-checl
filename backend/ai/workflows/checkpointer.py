"""LangGraph-Checkpointer: MongoDB (durable) oder Memory (Dev/Tests)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langgraph.checkpoint.memory import MemorySaver

if TYPE_CHECKING:
    from backend.core.config.settings import Settings

logger = logging.getLogger(__name__)


def build_checkpointer(settings: Settings) -> Any:
    """Erzeugt einen Checkpointer aus Settings."""
    if settings.web_use_memory_checkpointer:
        logger.info("LangGraph checkpointer: MemorySaver (WEB_USE_MEMORY_CHECKPOINTER)")
        return MemorySaver()

    uri = settings.langgraph_checkpoint_uri or settings.mongodb_uri
    if not uri:
        logger.warning(
            "Kein MongoDB-URI: LangGraph MemorySaver (Review nicht restart-sicher)"
        )
        return MemorySaver()

    try:
        from langgraph.checkpoint.mongodb import MongoDBSaver

        from backend.infrastructure.repositories.mongo import get_client

        client = get_client(settings)
        saver = MongoDBSaver(client, db_name=settings.mongodb_db_name)
        logger.info("LangGraph checkpointer: MongoDBSaver")
        return saver
    except Exception as exc:
        logger.warning("MongoDBSaver fehlgeschlagen, MemorySaver: %s", exc)
        return MemorySaver()


def clear_thread_checkpoints(
    checkpointer: Any,
    thread_id: str,
    *,
    checkpoint_ns: str = "",
) -> bool:
    """Löscht LangGraph-State für thread_id (Schema-Mismatch)."""
    collection = getattr(checkpointer, "checkpoint_collection", None)
    writes = getattr(checkpointer, "writes_collection", None)
    if collection is None or writes is None:
        return False
    query = {"thread_id": thread_id, "checkpoint_ns": checkpoint_ns}
    cp_result = collection.delete_many(query)
    writes_result = writes.delete_many(query)
    deleted = int(cp_result.deleted_count) + int(writes_result.deleted_count)
    if deleted:
        logger.info(
            "LangGraph checkpoints cleared for thread_id=%s (deleted=%s)",
            thread_id,
            deleted,
        )
    return deleted > 0
