"""Grounding-Heuristik für Antwortentwürfe."""

from __future__ import annotations

import re

from backend.ai.services.retrieval import RetrievalHits
from backend.core.models.response import GeneratedResponse

_BOOKING_REF = re.compile(r"\b[A-Z]{2}\d{3,}\b")


class GroundingService:
    """Prüft ob genannte Buchungsnummern in den Retrieval-Daten vorkommen."""

    def check(
        self,
        draft: GeneratedResponse,
        hits: RetrievalHits,
    ) -> bool:
        """True wenn keine verdächtigen Referenzen gefunden werden."""
        known: set[str] = set()
        if hits.reservations:
            for r in hits.reservations:
                if r.booking_number:
                    known.add(r.booking_number.upper())
        mentioned = {m.upper() for m in _BOOKING_REF.findall(draft.body)}
        if not mentioned:
            return True
        if not known:
            return False
        return mentioned.issubset(known)
