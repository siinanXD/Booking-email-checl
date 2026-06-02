"""Plattform-Admin: Account-Freischaltung."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, g, jsonify, request

from web.middleware.auth_guard import require_auth
from web.middleware.roles import require_platform_admin
from web.schemas.accounts import (
    AccountActionResponse,
    AccountListItem,
    AccountListResponse,
    AccountRejectRequest,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _to_list_item(account: object) -> AccountListItem:
    from repositories.account_repository import AccountRecord

    assert isinstance(account, AccountRecord)
    created = account.created_at.isoformat()
    return AccountListItem(
        id=account.id,
        display_name=account.display_name,
        contact_email=account.contact_email,
        account_type=account.account_type,
        company_name=account.company_name,
        phone=account.phone,
        status=account.status,
        rejection_reason=account.rejection_reason,
        created_at=created,
    )


@admin_bp.get("/accounts")
@require_auth
@require_platform_admin
def list_accounts() -> tuple[Any, int]:
    """Listet Accounts (Metadaten) – Filter: status=pending|active|..."""
    status = request.args.get("status")
    if status:
        accounts = g.ctx.account_repo.list_by_status(status)
    else:
        accounts = g.ctx.account_repo.list_by_status(None)
    items = [_to_list_item(a) for a in accounts]
    return (
        jsonify(AccountListResponse(items=items, total=len(items)).model_dump()),
        200,
    )


@admin_bp.post("/accounts/<account_id>/approve")
@require_auth
@require_platform_admin
def approve_account(account_id: str) -> tuple[Any, int]:
    """Schaltet einen Account frei."""
    account = g.ctx.account_repo.get_by_id(account_id)
    if account is None:
        return jsonify({"error": "Account not found", "code": 404}), 404
    if account.status == "active":
        return (
            jsonify(
                AccountActionResponse(
                    id=account_id,
                    status="active",
                    message="Account ist bereits freigeschaltet.",
                ).model_dump()
            ),
            200,
        )
    updated = g.ctx.account_repo.update_status(account_id, "active")
    if updated is None:
        return jsonify({"error": "Account not found", "code": 404}), 404
    return (
        jsonify(
            AccountActionResponse(
                id=account_id,
                status="active",
                message="Account freigeschaltet.",
            ).model_dump()
        ),
        200,
    )


@admin_bp.post("/accounts/<account_id>/reject")
@require_auth
@require_platform_admin
def reject_account(account_id: str) -> tuple[Any, int]:
    """Lehnt einen Account ab."""
    account = g.ctx.account_repo.get_by_id(account_id)
    if account is None:
        return jsonify({"error": "Account not found", "code": 404}), 404
    body = AccountRejectRequest.model_validate(request.get_json(silent=True) or {})
    updated = g.ctx.account_repo.update_status(
        account_id,
        "rejected",
        rejection_reason=body.reason,
    )
    if updated is None:
        return jsonify({"error": "Account not found", "code": 404}), 404
    return (
        jsonify(
            AccountActionResponse(
                id=account_id,
                status="rejected",
                message="Account abgelehnt.",
            ).model_dump()
        ),
        200,
    )
