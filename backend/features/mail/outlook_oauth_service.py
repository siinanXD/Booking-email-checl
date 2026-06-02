"""OAuth2 Authorization-Code-Flow für Outlook (Browser-Redirect)."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode

import msal

from backend.core.config.settings import Settings
from backend.infrastructure.adapters.outlook.auth import (
    DELEGATED_SCOPES,
    authority_host,
)
from backend.infrastructure.repositories.mail_connection_repository import (
    MailConnectionRepository,
)
from backend.infrastructure.repositories.outlook_oauth_flow_repository import (
    OutlookOAuthFlowRecord,
    OutlookOAuthFlowRepository,
)

logger = logging.getLogger(__name__)


class OutlookOAuthService:
    """Startet und schließt den MSAL Auth-Code-Flow pro Mandant ab."""

    def __init__(
        self,
        settings: Settings,
        mail_repo: MailConnectionRepository,
        flow_repo: OutlookOAuthFlowRepository,
    ) -> None:
        self._settings = settings
        self._mail_repo = mail_repo
        self._flow_repo = flow_repo

    def build_authorize_url(
        self,
        account_id: str,
        return_to: str,
        frontend_origin: str = "",
    ) -> str:
        """Erzeugt Microsoft-Login-URL und speichert pending Flow."""
        if not self._settings.azure_client_id:
            msg = "AZURE_CLIENT_ID ist nicht konfiguriert"
            raise ValueError(msg)
        app, _token_cache = self._msal_app()
        redirect_uri = self._resolve_redirect_uri()
        logger.info(
            "Outlook OAuth authorize: redirect_uri=%s client_id=%s account_id=%s",
            redirect_uri,
            self._settings.azure_client_id,
            account_id,
        )
        flow = app.initiate_auth_code_flow(
            scopes=DELEGATED_SCOPES,
            redirect_uri=redirect_uri,
            prompt="select_account",
        )
        if "auth_uri" not in flow:
            err = flow.get("error_description") or flow
            raise RuntimeError(f"OAuth-Flow konnte nicht gestartet werden: {err}")
        state = str(flow.get("state") or "")
        if not state:
            msg = "MSAL-Flow ohne state"
            raise RuntimeError(msg)
        self._flow_repo.save(
            OutlookOAuthFlowRecord(
                state=state,
                account_id=account_id,
                flow=flow,
                return_to=self._normalize_return_to(return_to),
                frontend_origin=self._normalize_frontend_origin(frontend_origin),
            )
        )
        return str(flow["auth_uri"])

    def complete_callback(
        self,
        query_params: dict[str, str],
    ) -> tuple[str, str | None]:
        """Tauscht Code gegen Tokens; liefert (redirect_url, error_message)."""
        state = query_params.get("state", "")
        pending = self._flow_repo.pop(state)
        if pending is None:
            return (
                self._frontend_redirect(
                    "/onboarding",
                    "error",
                    "Ungültiger OAuth-State",
                    self._settings.frontend_url,
                ),
                None,
            )

        frontend_base = pending.frontend_origin or self._settings.frontend_url

        if query_params.get("error"):
            err = query_params.get("error_description") or query_params.get("error")
            return (
                self._frontend_redirect(
                    pending.return_to, "error", str(err), frontend_base
                ),
                str(err),
            )

        app, token_cache = self._msal_app()
        callback_redirect = str(
            pending.flow.get("redirect_uri") or self._resolve_redirect_uri()
        )
        logger.info(
            "Outlook OAuth callback: flow_redirect_uri=%s client_id=%s state=%s",
            callback_redirect,
            self._settings.azure_client_id,
            state[:8] if state else "",
        )
        try:
            result = app.acquire_token_by_auth_code_flow(pending.flow, query_params)
        except Exception as exc:
            logger.exception("Outlook OAuth callback failed")
            return (
                self._frontend_redirect(
                    pending.return_to, "error", str(exc), frontend_base
                ),
                str(exc),
            )

        if not result or "access_token" not in result:
            err = (result or {}).get(
                "error_description"
            ) or "Token-Austausch fehlgeschlagen"
            return (
                self._frontend_redirect(
                    pending.return_to, "error", str(err), frontend_base
                ),
                str(err),
            )

        cache_json = token_cache.serialize()
        email = self._email_from_result(result)

        record = self._mail_repo.get_or_create(pending.account_id)
        record.provider = "outlook"
        record.outlook_auth_mode = "oauth"
        record.outlook_token_cache = cache_json
        if email:
            record.email_address = email
            record.outlook_mailbox = email
        record.status = "connected"
        record.last_error = None
        self._mail_repo.save(record)

        return (
            self._frontend_redirect(
                pending.return_to, "connected", None, frontend_base
            ),
            None,
        )

    def _msal_app(
        self,
    ) -> tuple[msal.ConfidentialClientApplication, msal.SerializableTokenCache]:
        client_id = self._settings.azure_client_id
        assert client_id
        secret = self._settings.azure_client_secret
        if not secret:
            msg = "AZURE_CLIENT_SECRET ist für den OAuth-Redirect-Flow erforderlich"
            raise ValueError(msg)
        token_cache = msal.SerializableTokenCache()
        app = msal.ConfidentialClientApplication(
            client_id,
            authority=authority_host(self._settings.azure_authority),
            client_credential=secret,
            token_cache=token_cache,
        )
        return app, token_cache

    def _resolve_redirect_uri(self) -> str:
        return self._settings.outlook_oauth_redirect_uri.replace(
            "127.0.0.1", "localhost"
        )

    @staticmethod
    def _email_from_result(result: dict[str, Any]) -> str:
        claims = result.get("id_token_claims") or {}
        for key in ("preferred_username", "email", "upn"):
            val = claims.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip().lower()
        return ""

    def _frontend_redirect(
        self,
        return_to: str,
        status: str,
        message: str | None,
        frontend_base: str | None = None,
    ) -> str:
        base = (frontend_base or self._settings.frontend_url).rstrip("/")
        path_part, _, query_part = return_to.partition("?")
        path = path_part if path_part.startswith("/") else f"/{path_part}"
        params = dict(parse_qsl(query_part, keep_blank_values=True))
        params["outlook"] = status
        if message:
            params["outlook_message"] = message[:200]
        query = urlencode(params, quote_via=quote)
        return f"{base}{path}?{query}"

    @staticmethod
    def _normalize_return_to(return_to: str) -> str:
        path = (return_to or "/onboarding").strip()
        if not path.startswith("/"):
            path = f"/{path}"
        return path

    def _normalize_frontend_origin(self, origin: str) -> str:
        value = origin.strip().rstrip("/")
        if value.startswith("http://") or value.startswith("https://"):
            return value
        return self._settings.frontend_url.rstrip("/")
