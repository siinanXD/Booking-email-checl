"""Einfache operative Alerts."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class AlertThresholds:
    """Schwellen für Alerts."""

    max_cost_per_mail_usd: float = 0.50
    grounding_failure_rate: float = 0.3
    max_draft_edit_distance: float = 0.4


class AlertService:
    """Loggt und sendet optional Webhook-Alerts."""

    def __init__(
        self,
        webhook_url: str | None = None,
        thresholds: AlertThresholds | None = None,
    ) -> None:
        """Initialize the instance with its dependencies."""
        self._webhook = webhook_url
        self._thresholds = thresholds or AlertThresholds()

    @property
    def thresholds(self) -> AlertThresholds:
        """Expose configured alert thresholds."""
        return self._thresholds

    def check_cost_per_mail(self, cost_usd: float, correlation_id: str) -> None:
        """Warnt bei hohen Kosten pro Mail."""
        if cost_usd > self._thresholds.max_cost_per_mail_usd:
            self._emit(
                "high_cost",
                {"correlation_id": correlation_id, "cost_usd": cost_usd},
            )

    def check_extraction_failure(self, correlation_id: str, error: str) -> None:
        """Meldet fehlgeschlagene Extraktion."""
        self._emit(
            "extraction_failure",
            {"correlation_id": correlation_id, "error": error},
        )

    def check_grounding_suspect(self, correlation_id: str) -> None:
        """Meldet Grounding-Verdacht."""
        self._emit("grounding_suspect", {"correlation_id": correlation_id})

    def check_retrieval_empty(self, correlation_id: str, reason: str) -> None:
        """Warnt wenn Retrieval keine Treffer liefert obwohl Buchungsnummer bekannt."""
        self._emit(
            "retrieval_empty",
            {"correlation_id": correlation_id, "reason": reason},
        )

    def check_draft_quality(self, correlation_id: str, distance: float) -> None:
        """Warnt wenn Draft stark vom freigegebenen Text abweicht."""
        self._emit(
            "draft_quality_low",
            {"correlation_id": correlation_id, "edit_distance": distance},
        )

    def _emit(self, alert_type: str, payload: dict[str, Any]) -> None:
        message = f"[ALERT] {alert_type}: {payload}"
        logger.warning(message)
        if self._webhook:
            try:
                httpx.post(
                    self._webhook,
                    json={"type": alert_type, **payload},
                    timeout=5.0,
                )
            except httpx.HTTPError as exc:
                logger.error("Webhook alert failed: %s", exc)
