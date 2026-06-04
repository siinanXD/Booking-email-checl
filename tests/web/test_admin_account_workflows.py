"""Plattform-Admin: Workflows pro Mandant."""

from __future__ import annotations

from typing import Any


def test_admin_manages_tenant_workflows(
    client: Any,
    auth_headers: dict[str, str],
    tenant_owner_auth_headers: dict[str, str],
) -> None:
    tenant_create = client.post(
        "/api/workflows",
        headers=tenant_owner_auth_headers,
        json={
            "label": "Tenant Workflow",
            "slug": "tenant_slug",
            "description": "From tenant",
            "extract_prompt": "Extrahiere JSON: {subject} {body}",
            "sandbox_only": True,
        },
    )
    assert tenant_create.status_code == 201
    tenant_account_id = tenant_create.get_json()["account_id"]

    admin_list = client.get(
        f"/api/admin/accounts/{tenant_account_id}/workflows",
        headers=auth_headers,
    )
    assert admin_list.status_code == 200
    assert len(admin_list.get_json()["items"]) >= 1

    admin_create = client.post(
        f"/api/admin/accounts/{tenant_account_id}/workflows",
        headers=auth_headers,
        json={
            "label": "Admin Created",
            "slug": "admin_created",
            "description": "From platform admin",
            "extract_prompt": "Extrahiere JSON: {subject} {body}",
            "sandbox_only": True,
        },
    )
    assert admin_create.status_code == 201
    workflow_id = admin_create.get_json()["id"]

    preview = client.post(
        f"/api/admin/accounts/{tenant_account_id}/workflows/{workflow_id}/preview",
        headers=auth_headers,
        json={"subject": "Test", "body": "Extrahiere strukturierte Daten"},
    )
    assert preview.status_code == 200
    assert preview.get_json()["success"] is True


def test_admin_workflows_forbidden_for_tenant(
    client: Any,
    tenant_owner_auth_headers: dict[str, str],
) -> None:
    me = client.get("/api/auth/me", headers=tenant_owner_auth_headers)
    account_id = me.get_json()["account_id"]
    resp = client.get(
        f"/api/admin/accounts/{account_id}/workflows",
        headers=tenant_owner_auth_headers,
    )
    assert resp.status_code == 403


def test_admin_workflows_unknown_account(
    client: Any,
    auth_headers: dict[str, str],
) -> None:
    resp = client.get(
        "/api/admin/accounts/nonexistent/workflows",
        headers=auth_headers,
    )
    assert resp.status_code == 404
