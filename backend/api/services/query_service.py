"""Lesezugriffe für Dashboard und Listen — Facade."""

from __future__ import annotations

from backend.api.schemas.costs import CostsResponse
from backend.api.schemas.dashboard import DashboardStats
from backend.api.schemas.emails import EmailDetail, EmailListResponse
from backend.api.schemas.review import ReviewQueueItem
from backend.api.services import dashboard_queries, email_queries
from backend.core.config.factory import AppContext


class QueryService:
    """Aggregationen und Mapping für die Web-API."""

    def __init__(self, ctx: AppContext, account_id: str) -> None:
        self._ctx = ctx
        self._account_id = account_id

    def dashboard_stats(self) -> DashboardStats:
        return dashboard_queries.dashboard_stats(self._ctx, self._account_id)

    def demo_stats(self) -> DashboardStats:
        return dashboard_queries.demo_stats()

    def list_emails(
        self,
        *,
        status: str | None,
        intent: str | None,
        intents: list[str] | None,
        platform: str | None,
        search: str | None,
        booking_related: bool,
        page: int,
        limit: int,
    ) -> EmailListResponse:
        return email_queries.list_emails(
            self._ctx,
            self._account_id,
            status=status,
            intent=intent,
            intents=intents,
            platform=platform,
            search=search,
            booking_related=booking_related,
            page=page,
            limit=limit,
        )

    def get_email_detail(self, correlation_id: str) -> EmailDetail | None:
        return email_queries.get_email_detail(
            self._ctx,
            self._account_id,
            correlation_id,
        )

    def list_review_pending(self, *, limit: int = 50) -> list[ReviewQueueItem]:
        return email_queries.list_review_pending(
            self._ctx,
            self._account_id,
            limit=limit,
        )

    def costs(
        self,
        *,
        from_date: str | None,
        to_date: str | None,
        group_by: str,
    ) -> CostsResponse:
        return dashboard_queries.costs(
            self._ctx,
            self._account_id,
            from_date=from_date,
            to_date=to_date,
            group_by=group_by,
        )
