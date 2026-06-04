"""Gemini-/Multimodal-Tests für Mandanten-Workflows."""

from __future__ import annotations

from typing import Any

from tests.conftest import TINY_PNG_B64


def test_gemini_status_endpoint(
    client: Any,
    tenant_owner_auth_headers: dict[str, str],
    auth_headers: dict[str, str],
) -> None:
    tenant_resp = client.get(
        "/api/workflows/gemini-status", headers=tenant_owner_auth_headers
    )
    assert tenant_resp.status_code == 403
    me = client.get("/api/auth/me", headers=tenant_owner_auth_headers)
    account_id = me.get_json()["account_id"]
    resp = client.get(
        f"/api/admin/accounts/{account_id}/workflows/gemini-status",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["available"] is True
    assert "gemini" in data["model"]


def test_suggest_from_example_screenshot_mock(
    client: Any,
    tenant_owner_auth_headers: dict[str, str],
    auth_headers: dict[str, str],
) -> None:
    me = client.get("/api/auth/me", headers=tenant_owner_auth_headers)
    account_id = me.get_json()["account_id"]
    suggest = client.post(
        f"/api/admin/accounts/{account_id}/workflows/suggest",
        headers=auth_headers,
        json={
            "description": "Tracking-Mails erkennen",
            "label_hint": "Tracking",
            "attachments": [
                {
                    "filename": "mail.png",
                    "mime_type": "image/png",
                    "data_base64": TINY_PNG_B64,
                }
            ],
        },
    )
    assert suggest.status_code == 200
    draft = suggest.get_json()
    assert draft["supports_multimodal"] is True
    assert draft["llm_provider"] == "gemini"
    assert draft["match_rules"]["subject_keywords"]
    assert draft["test_emails"]
    assert draft["test_emails"][0]["attachments"]
    assert "tracking" in draft["slug"].lower() or "tracking" in draft["label"].lower()


def test_suggest_requires_description_without_attachment(
    client: Any,
    tenant_owner_auth_headers: dict[str, str],
    auth_headers: dict[str, str],
) -> None:
    me = client.get("/api/auth/me", headers=tenant_owner_auth_headers)
    account_id = me.get_json()["account_id"]
    resp = client.post(
        f"/api/admin/accounts/{account_id}/workflows/suggest",
        headers=auth_headers,
        json={"description": "kurz"},
    )
    assert resp.status_code == 422


def test_gemini_multimodal_preview_mock(
    client: Any,
    tenant_owner_auth_headers: dict[str, str],
    auth_headers: dict[str, str],
) -> None:
    me = client.get("/api/auth/me", headers=tenant_owner_auth_headers)
    account_id = me.get_json()["account_id"]
    create = client.post(
        f"/api/admin/accounts/{account_id}/workflows",
        headers=auth_headers,
        json={
            "label": "Gemini WF",
            "slug": "gemini_wf",
            "description": "Multimodal test",
            "extract_prompt": (
                "Extrahiere JSON mit reference_id und summary: {subject} {body}"
            ),
            "multimodal_prompt": "Lies auch Anhänge.",
            "llm_provider": "gemini",
            "supports_multimodal": True,
            "sandbox_only": True,
        },
    )
    assert create.status_code == 201
    workflow_id = create.get_json()["id"]
    preview = client.post(
        f"/api/admin/accounts/{account_id}/workflows/{workflow_id}/preview",
        headers=auth_headers,
        json={
            "subject": "Rechnung",
            "body": "Siehe Anhang",
            "attachments": [
                {
                    "filename": "pixel.png",
                    "mime_type": "image/png",
                    "data_base64": TINY_PNG_B64,
                }
            ],
        },
    )
    assert preview.status_code == 200
    data = preview.get_json()
    assert data["success"] is True
    assert data["model"] == "gemini-2.0-flash"
    assert "reference_id" in (data["result"] or "")


def test_preview_invalid_mime_rejected(
    client: Any,
    tenant_owner_auth_headers: dict[str, str],
    auth_headers: dict[str, str],
) -> None:
    me = client.get("/api/auth/me", headers=tenant_owner_auth_headers)
    account_id = me.get_json()["account_id"]
    create = client.post(
        f"/api/admin/accounts/{account_id}/workflows",
        headers=auth_headers,
        json={
            "label": "Bad MIME",
            "slug": "bad_mime",
            "description": "Test",
            "extract_prompt": "Extrahiere JSON: {subject} {body}",
            "sandbox_only": True,
        },
    )
    assert create.status_code == 201
    workflow_id = create.get_json()["id"]
    preview = client.post(
        f"/api/admin/accounts/{account_id}/workflows/{workflow_id}/preview",
        headers=auth_headers,
        json={
            "attachments": [
                {
                    "filename": "evil.exe",
                    "mime_type": "application/octet-stream",
                    "data_base64": "AAAA",
                }
            ],
        },
    )
    assert preview.status_code == 422
