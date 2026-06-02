"""Microsoft Graph: Auth, Abruf und Mapping nach IncomingEmail."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import msal

from config.settings import Settings
from models.email import IncomingEmail

logger = logging.getLogger(__name__)

GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
# MSAL ergänzt openid/profile/offline_access selbst – nicht explizit angeben.
DELEGATED_SCOPES = [
    "https://graph.microsoft.com/User.Read",
    "https://graph.microsoft.com/Mail.Read",
]
APPLICATION_SCOPE = ["https://graph.microsoft.com/.default"]

_MESSAGE_SELECT = (
    "id,internetMessageId,subject,from,toRecipients,receivedDateTime,"
    "body,internetMessageHeaders"
)


def _authority_host(authority: str) -> str:
    segment = authority.strip().strip("/")
    if segment in ("common", "consumers", "organizations") or len(segment) == 36:
        return f"https://login.microsoftonline.com/{segment}"
    if segment.startswith("https://"):
        return segment.rstrip("/")
    return f"https://login.microsoftonline.com/{segment}"


def _parse_received_at(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text).astimezone(UTC)


def _header_value(headers: list[dict[str, str]] | None, name: str) -> str | None:
    if not headers:
        return None
    target = name.lower()
    for item in headers:
        if (item.get("name") or "").lower() == target:
            raw = item.get("value")
            return raw.strip() if raw else None
    return None


def _parse_references(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in re.split(r"\s+", raw.strip()) if part.strip()]


def map_graph_message(graph_msg: dict[str, Any]) -> IncomingEmail:
    """Mappt eine Graph message-Ressource auf IncomingEmail."""
    message_id = graph_msg.get("internetMessageId") or graph_msg.get("id") or ""
    if not message_id:
        msg = "Graph message lacks internetMessageId and id"
        raise ValueError(msg)

    from_block = graph_msg.get("from") or {}
    from_addr = (from_block.get("emailAddress") or {}).get("address") or ""

    to_addresses: list[str] = []
    for recipient in graph_msg.get("toRecipients") or []:
        addr = (recipient.get("emailAddress") or {}).get("address")
        if addr:
            to_addresses.append(addr)

    body = graph_msg.get("body") or {}
    content_type = (body.get("contentType") or "text").lower()
    content = body.get("content") or ""
    body_text = content if content_type == "text" else ""
    body_html = content if content_type == "html" else None

    headers = graph_msg.get("internetMessageHeaders")
    in_reply_to = _header_value(headers, "In-Reply-To")
    references = _parse_references(_header_value(headers, "References"))

    received_raw = graph_msg.get("receivedDateTime")
    if not received_raw:
        msg = "Graph message lacks receivedDateTime"
        raise ValueError(msg)

    return IncomingEmail(
        message_id=message_id,
        from_address=from_addr,
        to_addresses=to_addresses,
        subject=graph_msg.get("subject") or "",
        body_text=body_text,
        body_html=body_html,
        received_at=_parse_received_at(received_raw),
        in_reply_to=in_reply_to,
        references=references,
        platform="outlook",
    )


@dataclass
class _TokenState:
    access_token: str


class DelegatedAuth:
    """Device Code + MSAL-Token-Cache (wiederholte Läufe ohne Re-Login)."""

    def __init__(
        self,
        client_id: str,
        authority: str,
        cache_path: Path,
    ) -> None:
        self._client_id = client_id
        self._authority = _authority_host(authority)
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


class OutlookGraphClient:
    """Graph REST-Client für Inbox-Ungelesen und Nachbearbeitung."""

    def __init__(
        self,
        *,
        auth_mode: str,
        mailbox: str | None,
        token_provider: DelegatedAuth | ApplicationAuth,
    ) -> None:
        mode = auth_mode.strip().lower()
        if mode not in ("delegated", "application"):
            msg = f"Unsupported OUTLOOK_AUTH_MODE: {auth_mode}"
            raise ValueError(msg)
        self._auth_mode = mode
        self._mailbox = mailbox
        self._token_provider = token_provider
        self._token: str | None = None

    @classmethod
    def from_settings(cls, settings: Settings) -> OutlookGraphClient:
        if not settings.azure_client_id:
            msg = "AZURE_CLIENT_ID is required for Outlook ingestion"
            raise ValueError(msg)
        mode = settings.outlook_auth_mode.strip().lower()
        if mode == "application":
            if not settings.azure_tenant_id:
                msg = "AZURE_TENANT_ID is required for application auth"
                raise ValueError(msg)
            if not settings.azure_client_secret:
                msg = "AZURE_CLIENT_SECRET is required for application auth"
                raise ValueError(msg)
            if not settings.outlook_mailbox:
                msg = "OUTLOOK_MAILBOX is required for application auth"
                raise ValueError(msg)
            token_provider: DelegatedAuth | ApplicationAuth = ApplicationAuth(
                settings.azure_tenant_id,
                settings.azure_client_id,
                settings.azure_client_secret,
            )
        else:
            token_provider = DelegatedAuth(
                settings.azure_client_id,
                settings.azure_authority,
                Path(settings.outlook_token_cache_path),
            )
        return cls(
            auth_mode=mode,
            mailbox=settings.outlook_mailbox,
            token_provider=token_provider,
        )

    def _resource_prefix(self) -> str:
        if self._auth_mode == "application":
            assert self._mailbox
            return f"users/{quote(self._mailbox, safe='')}"
        return "me"

    def _access_token(self) -> str:
        if self._token is None:
            self._token = self._token_provider.get_token()
        return self._token

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        query = f"?{urlencode(params)}" if params else ""
        url = f"{GRAPH_ROOT}/{path.lstrip('/')}{query}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {
            "Authorization": f"Bearer {self._access_token()}",
            "Accept": "application/json",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8")
                if not raw:
                    return {}
                return cast(dict[str, Any], json.loads(raw))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Graph {method} {path} failed ({exc.code}): {detail}"
            ) from exc

    def list_inbox_messages(
        self,
        top: int = 100,
        *,
        unread_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Neueste Mails aus dem Posteingang (neueste zuerst, begrenzt durch top)."""
        prefix = self._resource_prefix()
        params: dict[str, str] = {
            "$top": str(top),
            "$select": _MESSAGE_SELECT,
            "$orderby": "receivedDateTime desc",
        }
        if unread_only:
            params["$filter"] = "isRead eq false"
        path = f"{prefix}/mailFolders/inbox/messages"
        payload = self._request("GET", path, params=params)
        return list(payload.get("value") or [])

    def list_unread_inbox_messages(self, top: int = 50) -> list[dict[str, Any]]:
        """Ungelesene Mails (Kompatibilität); bevorzugt list_inbox_messages nutzen."""
        return self.list_inbox_messages(top, unread_only=True)

    def mark_message_read(self, graph_id: str) -> None:
        prefix = self._resource_prefix()
        path = f"{prefix}/messages/{quote(graph_id, safe='')}"
        self._request("PATCH", path, body={"isRead": True})

    def move_message_to_folder(self, graph_id: str, folder_display_name: str) -> None:
        folder_id = self._resolve_folder_id(folder_display_name)
        prefix = self._resource_prefix()
        path = f"{prefix}/messages/{quote(graph_id, safe='')}/move"
        self._request("POST", path, body={"destinationId": folder_id})

    def _resolve_folder_id(self, display_name: str) -> str:
        prefix = self._resource_prefix()
        params = {"$filter": f"displayName eq '{display_name}'", "$select": "id"}
        payload = self._request("GET", f"{prefix}/mailFolders", params=params)
        folders = payload.get("value") or []
        if not folders:
            msg = f"Mail folder not found: {display_name}"
            raise ValueError(msg)
        return str(folders[0]["id"])

    def post_process_message(
        self,
        graph_id: str,
        *,
        action: str,
        processed_folder: str | None,
    ) -> None:
        """Nach erfolgreicher Ingestion: none, mark_read oder move."""
        act = action.strip().lower()
        if act in ("", "none", "skip"):
            return
        if act == "move":
            if not processed_folder:
                msg = "OUTLOOK_PROCESSED_FOLDER required when OUTLOOK_POST_ACTION=move"
                raise ValueError(msg)
            self.move_message_to_folder(graph_id, processed_folder)
            return
        if act == "mark_read":
            self.mark_message_read(graph_id)
            return
        msg = f"Unsupported OUTLOOK_POST_ACTION: {action!r} (use none, mark_read, move)"
        raise ValueError(msg)
