"""Validierung Workflow-Medien-Anhänge."""

from __future__ import annotations

import base64

import pytest
from pydantic import ValidationError

from backend.core.models.workflow_media import WorkflowMediaAttachment


def test_workflow_media_attachment_accepts_png() -> None:
    raw = b"\x89PNG\r\n\x1a\n"
    att = WorkflowMediaAttachment(
        filename="x.png",
        mime_type="image/png",
        data_base64=base64.b64encode(raw).decode("ascii"),
    )
    assert att.mime_type == "image/png"


def test_workflow_media_attachment_rejects_bad_mime() -> None:
    with pytest.raises(ValidationError):
        WorkflowMediaAttachment(
            filename="x.bin",
            mime_type="application/octet-stream",
            data_base64="AAAA",
        )
