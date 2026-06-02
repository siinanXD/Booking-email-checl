"""OpenAI Chat-Client; mit Langfuse-Wrapper wenn Tracing aktiv."""

from __future__ import annotations

from typing import Any, cast

from services.llm_types import LLMCompletion


def _chat_openai_module(*, use_langfuse: bool) -> type[Any]:
    if use_langfuse:
        from langfuse.openai import OpenAI as LangfuseOpenAI

        return cast(type[Any], LangfuseOpenAI)
    from openai import OpenAI

    return cast(type[Any], OpenAI)


class OpenAIClient:
    """OpenAI Chat Completions; Langfuse loggt Aufrufe automatisch (live + Tracing)."""

    def __init__(self, api_key: str, *, use_langfuse: bool = False) -> None:
        client_cls = _chat_openai_module(use_langfuse=use_langfuse)
        self._client = client_cls(api_key=api_key)

    def complete(self, prompt: str, model: str) -> LLMCompletion:
        response = self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content or ""
        usage = response.usage
        return LLMCompletion(
            text=content.strip(),
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
        )
