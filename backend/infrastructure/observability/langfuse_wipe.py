"""DSGVO-konforme Langfuse-Trace-Löschung pro Mandant."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_MAX_TRACES_PER_SESSION = 50  # Langfuse-Paginierung; reicht für eine Mail


class LangfuseWipeService:
    """Löscht Langfuse-Traces für eine Liste von session_ids (= correlation_ids).

    Wird aus DataWipeService aufgerufen, wenn Langfuse aktiviert ist.
    Fehler (Netz, API-Limit) werden geloggt, aber kein Rollback — Mongo-Wipe
    ist bereits abgeschlossen. Operator muss ggf. manuell nachbereinigen.
    """

    def __init__(
        self,
        public_key: str | None,
        secret_key: str | None,
        host: str | None = None,
    ) -> None:
        """Initialize with Langfuse credentials."""
        self._client: Any = None
        if public_key and secret_key:
            try:
                from langfuse import Langfuse

                self._client = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=host or "https://cloud.langfuse.com",
                )
            except Exception:
                logger.warning("Langfuse-Client konnte nicht initialisiert werden.")

    def delete_traces_for_sessions(self, session_ids: list[str]) -> int:
        """Löscht alle Traces für die angegebenen session_ids.

        Args:
            session_ids: Liste von correlation_ids (= Langfuse session_id).

        Returns:
            Anzahl erfolgreich gelöschter Traces.
        """
        if self._client is None or not session_ids:
            return 0

        deleted = 0
        for session_id in session_ids:
            try:
                result = self._client.fetch_traces(
                    session_id=session_id,
                    limit=_MAX_TRACES_PER_SESSION,
                )
                for trace in result.data:
                    try:
                        self._client.client.trace.delete(trace_id=trace.id)
                        deleted += 1
                    except Exception as exc:
                        logger.warning(
                            "Langfuse: Trace %s konnte nicht gelöscht werden: %s",
                            trace.id,
                            exc,
                        )
            except Exception as exc:
                logger.warning(
                    "Langfuse: Traces für session %s nicht abrufbar: %s",
                    session_id,
                    exc,
                )
        return deleted
