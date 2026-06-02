"""API-Helfer für mandantenspezifische QueryService-Instanzen."""

from __future__ import annotations

from flask import g

from config.factory import AppContext
from web.middleware.tenant import get_request_account_id
from web.services.query_service import QueryService


def tenant_query_service(ctx: AppContext | None = None) -> QueryService:
    """QueryService für den Account aus dem JWT."""
    app_ctx = ctx or g.ctx
    account_id = get_request_account_id()
    if not account_id:
        msg = "Account context required"
        raise RuntimeError(msg)
    return QueryService(app_ctx, account_id)
