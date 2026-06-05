"""Properties-API-Tests."""

from __future__ import annotations

from typing import Any


def test_property_recipients_roundtrip(
    client: Any,
    auth_headers: dict[str, str],
    tenant_account_id: str,
) -> None:
    put_resp = client.put(
        "/api/properties/recipients",
        json={
            "items": [
                {"property_name": "Haus A", "phones": ["+491701234567"]},
            ]
        },
        headers=auth_headers,
    )
    assert put_resp.status_code == 200
    get_resp = client.get("/api/properties/recipients", headers=auth_headers)
    assert get_resp.status_code == 200
    data = get_resp.get_json()
    assert any(i["property_name"] == "Haus A" for i in data["items"])


def test_property_suggestions_empty_ok(
    client: Any,
    auth_headers: dict[str, str],
) -> None:
    resp = client.get("/api/properties/suggestions", headers=auth_headers)
    assert resp.status_code == 200
    assert "items" in resp.get_json()
