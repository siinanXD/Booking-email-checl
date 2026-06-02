"""Map Microsoft Graph messages to IncomingEmail."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from backend.core.models.email import IncomingEmail


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
