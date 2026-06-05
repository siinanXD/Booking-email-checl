"""Fallähnlichkeit über Vektorindex (nur Atlas Vector Search)."""

from __future__ import annotations

import logging
from typing import Any

from backend.ai.services.indexing import EmbeddingFn
from backend.infrastructure.repositories.embedding_repository import EmbeddingRepository
from backend.infrastructure.repositories.tenant_scope import with_account_filter

logger = logging.getLogger(__name__)


class SimilaritySearchService:
    """Optionale Ähnlichkeitssuche – nicht blockierend für Antwortpfad.

    Läuft ausschließlich über MongoDB Atlas Vector Search. Es gibt bewusst
    keine lokale In-Memory-Suche: Ist Atlas deaktiviert (``use_atlas=False``)
    oder die Vektordatenbank offline, wird die Suche übersprungen und eine
    leere Liste zurückgegeben (Warnung im Log). So kann nie die gesamte
    Embedding-Collection in den RAM geladen werden.
    """

    def __init__(
        self,
        embedding_repo: EmbeddingRepository,
        embed_client: EmbeddingFn,
        *,
        use_atlas: bool = False,
    ) -> None:
        """Initialize the instance with its dependencies."""
        self._repo = embedding_repo
        self._embed = embed_client
        self._use_atlas = use_atlas

    def find_similar_cases(
        self,
        query_text: str,
        limit: int = 5,
        filter: dict[str, Any] | None = None,
        *,
        account_id: str | None = None,
    ) -> list[dict[str, object]]:
        """Sucht ähnliche historische Fälle über Atlas Vector Search.

        Returns:
            Liste ähnlicher Chunks, oder leere Liste wenn Atlas deaktiviert
            bzw. die Vektordatenbank nicht erreichbar ist.
        """
        if not self._use_atlas:
            logger.warning(
                "vektorsuche_deaktiviert: SIMILARITY_USE_ATLAS=false – "
                "Fallähnlichkeit wird übersprungen (keine lokale Suche)."
            )
            return []

        scoped_filter = with_account_filter(filter or {}, account_id)
        vector = self._embed.embed(query_text)
        return self._repo.search_by_vector_atlas(
            vector,
            limit=limit,
            filter=scoped_filter or None,
        )
