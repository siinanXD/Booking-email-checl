"""Aggregierte Token-Kosten pro verarbeiteter Mail."""

from __future__ import annotations

from langfuse.decorators import langfuse_context

from observability.alerts import AlertService
from services.llm_types import LLMCompletion


class MailCostTracker:
    """Sammelt LLM-Token pro correlation_id; finalize meldet Gesamtkosten."""

    def __init__(
        self,
        cost_per_1k_tokens_usd: float = 0.002,
        alerts: AlertService | None = None,
        *,
        tracing: bool = False,
    ) -> None:
        self._cost_per_1k = cost_per_1k_tokens_usd
        self._alerts = alerts
        self._tracing = tracing
        self._prompt_tokens: dict[str, int] = {}
        self._completion_tokens: dict[str, int] = {}

    def add(self, correlation_id: str, completion: LLMCompletion) -> None:
        """Erfasst Token eines LLM-Aufrufs für diese Mail."""
        self._prompt_tokens[correlation_id] = (
            self._prompt_tokens.get(correlation_id, 0) + completion.prompt_tokens
        )
        self._completion_tokens[correlation_id] = (
            self._completion_tokens.get(correlation_id, 0)
            + completion.completion_tokens
        )

    def total_tokens(self, correlation_id: str) -> int:
        """Summe Prompt- und Completion-Tokens für eine Mail."""
        return self._prompt_tokens.get(correlation_id, 0) + self._completion_tokens.get(
            correlation_id, 0
        )

    def cost_usd(self, correlation_id: str) -> float:
        """Geschätzte Kosten in USD für eine Mail."""
        return (self.total_tokens(correlation_id) / 1000.0) * self._cost_per_1k

    def finalize(self, correlation_id: str) -> float:
        """Meldet Gesamtkosten (Alert + Langfuse-Trace-Metadaten); leert den Akku."""
        cost = self.cost_usd(correlation_id)
        usage = {
            "prompt_tokens": self._prompt_tokens.get(correlation_id, 0),
            "completion_tokens": self._completion_tokens.get(correlation_id, 0),
            "total_tokens": self.total_tokens(correlation_id),
            "cost_usd": cost,
        }
        if self._tracing and usage["total_tokens"] > 0:
            langfuse_context.update_current_trace(
                session_id=correlation_id,
                metadata={"mail_cost": usage},
            )
        if self._alerts is not None and usage["total_tokens"] > 0:
            self._alerts.check_cost_per_mail(cost, correlation_id)
        self._prompt_tokens.pop(correlation_id, None)
        self._completion_tokens.pop(correlation_id, None)
        return cost
