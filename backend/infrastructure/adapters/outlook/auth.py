"""MSAL authentication for Microsoft Graph."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import msal

logger = logging.getLogger(__name__)

DELEGATED_SCOPES = [
    "https://graph.microsoft.com/User.Read",
    "https://graph.microsoft.com/Mail.Read",
]
APPLICATION_SCOPE = ["https://graph.microsoft.com/.default"]


def authority_host(authority: str) -> str:
    segment = authority.strip().strip("/")
    if segment in ("common", "consumers", "organizations") or len(segment) == 36:
        return f"https://login.microsoftonline.com/{segment}"
    if segment.startswith("https://"):
        return segment.rstrip("/")
    return f"https://login.microsoftonline.com/{segment}"


class CachedDelegatedAuth:
    """OAuth Authorization-Code: MSAL-Cache pro Mandant (DB)."""

    def __init__(
        self,
        client_id: str,
        authority: str,
        client_secret: str,
        cache_json: str,
    ) -> None:
        self._client_id = client_id
        self._authority = authority_host(authority)
        self._client_secret = client_secret
        self._cache = msal.SerializableTokenCache()
        if cache_json.strip():
            self._cache.deserialize(cache_json)

    def get_token(self) -> str:
        app = msal.ConfidentialClientApplication(
            self._client_id,
            authority=self._authority,
            client_credential=self._client_secret,
            token_cache=self._cache,
        )
        accounts = app.get_accounts()
        if not accounts:
            msg = "Kein Microsoft-Konto verbunden. Bitte erneut anmelden."
            raise RuntimeError(msg)
        result = app.acquire_token_silent(DELEGATED_SCOPES, account=accounts[0])
        if not result or "access_token" not in result:
            err = (result or {}).get("error_description") or "Token refresh failed"
            raise RuntimeError(f"Outlook OAuth token failed: {err}")
        return str(result["access_token"])


class DelegatedAuth:
    """Device Code + MSAL-Token-Cache (wiederholte Läufe ohne Re-Login)."""

    def __init__(
        self,
        client_id: str,
        authority: str,
        cache_path: Path,
    ) -> None:
        self._client_id = client_id
        self._authority = authority_host(authority)
        self._cache_path = cache_path
        self._cache = msal.SerializableTokenCache()
        if cache_path.is_file():
            self._cache.deserialize(cache_path.read_text(encoding="utf-8"))

    def get_token(self) -> str:
        app = msal.PublicClientApplication(
            self._client_id,
            authority=self._authority,
            token_cache=self._cache,
        )
        accounts = app.get_accounts()
        result: dict[str, Any] | None = None
        if accounts:
            result = app.acquire_token_silent(DELEGATED_SCOPES, account=accounts[0])
            if result and "access_token" in result:
                logger.info(
                    "Microsoft-Anmeldung aus Token-Cache (%s)",
                    self._cache_path,
                )
        if not result or "access_token" not in result:
            logger.warning(
                "Kein gueltiger Cache – Device-Code-Login (danach: %s)",
                self._cache_path,
            )
            flow = app.initiate_device_flow(scopes=DELEGATED_SCOPES)
            if "user_code" not in flow:
                err = flow.get("error_description") or flow
                raise RuntimeError(f"Device flow failed: {err}")
            print(flow["message"])
            result = app.acquire_token_by_device_flow(flow)
        if not result or "access_token" not in result:
            err = (result or {}).get("error_description") or (result or {}).get("error")
            raise RuntimeError(f"Delegated token failed: {err}")
        self._persist_cache()
        return str(result["access_token"])

    def _persist_cache(self) -> None:
        if self._cache.has_state_changed:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._cache_path.write_text(self._cache.serialize(), encoding="utf-8")


class ApplicationAuth:
    """Client Credentials für App-only Zugriff auf ein Postfach."""

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
    ) -> None:
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret

    def get_token(self) -> str:
        authority = f"https://login.microsoftonline.com/{self._tenant_id}"
        app = msal.ConfidentialClientApplication(
            self._client_id,
            authority=authority,
            client_credential=self._client_secret,
        )
        result = app.acquire_token_for_client(scopes=APPLICATION_SCOPE)
        if not result or "access_token" not in result:
            err = (result or {}).get("error_description") or (result or {}).get("error")
            raise RuntimeError(f"Application token failed: {err}")
        return str(result["access_token"])
