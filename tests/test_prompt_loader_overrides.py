"""Prompt-Loader mit DB-Overrides."""

from __future__ import annotations

from backend.ai.services.prompt_loader import (
    format_resolved_prompt,
    load_prompt,
    resolve_prompt_text,
)


def test_resolve_prompt_text_uses_override() -> None:
    override = "Custom {subject} template"
    text = resolve_prompt_text("booking/classify.md", override)
    assert text == override


def test_resolve_prompt_text_falls_back_to_file() -> None:
    file_text = load_prompt("booking/classify.md")
    assert resolve_prompt_text("booking/classify.md", None) == file_text
    assert resolve_prompt_text("booking/classify.md", "   ") == file_text


def test_format_resolved_prompt_with_override() -> None:
    result = format_resolved_prompt(
        "booking/classify.md",
        "Betreff: {subject}",
        subject="Test",
    )
    assert result == "Betreff: Test"
