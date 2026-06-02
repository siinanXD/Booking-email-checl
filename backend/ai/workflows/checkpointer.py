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
