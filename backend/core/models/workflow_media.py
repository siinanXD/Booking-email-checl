"""Medien-Anhänge für Workflow-Preview/Tests (Phase C)."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass

from pydantic import BaseModel, Field, field_validator

MAX_ATTACHMENT_BYTES = 4 * 1024 * 1024
MAX_ATTACHMENTS_PER_REQUEST = 5
MAX_BASE64_CHARS = (MAX_ATTACHMENT_BYTES * 4 + 2) // 3 + 4

ALLOWED_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
    }
)


@dataclass(frozen=True)
class MediaPart:
    """Binärteil für Gemini-Multimodal."""

    mime_type: str
    data: bytes
    filename: str = ""


class WorkflowMediaAttachment(BaseModel):
    """Base64-Anhang in API-Requests."""

    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=3, max_length=128)
    data_base64: str = Field(min_length=1, max_length=MAX_BASE64_CHARS)

    @field_validator("mime_type")
    @classmethod
    def validate_mime(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_MIME_TYPES:
            msg = f"Unsupported mime_type: {value!r}"
            raise ValueError(msg)
        return normalized

    @field_validator("data_base64")
    @classmethod
    def validate_payload(cls, value: str) -> str:
        try:
            raw = base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError) as exc:
            msg = "Invalid base64 in data_base64"
            raise ValueError(msg) from exc
        if len(raw) > MAX_ATTACHMENT_BYTES:
            msg = f"Attachment exceeds {MAX_ATTACHMENT_BYTES} bytes"
            raise ValueError(msg)
        return value

    def to_media_part(self) -> MediaPart:
        raw = base64.b64decode(self.data_base64, validate=True)
        return MediaPart(
            mime_type=self.mime_type,
            data=raw,
            filename=self.filename,
        )


def attachments_to_media_parts(
    attachments: list[WorkflowMediaAttachment] | None,
) -> list[MediaPart]:
    """Konvertiert API-Anhänge in MediaPart-Liste."""
    if not attachments:
        return []
    if len(attachments) > MAX_ATTACHMENTS_PER_REQUEST:
        msg = f"At most {MAX_ATTACHMENTS_PER_REQUEST} attachments allowed"
        raise ValueError(msg)
    return [item.to_media_part() for item in attachments]
