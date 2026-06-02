"""Legacy-Wrapper – bevorzugt langfuse_setup + @observe (siehe docs/LANGFUSE.md)."""

from __future__ import annotations

from observability.langfuse_setup import configure_langfuse_env, tracing_enabled

__all__ = ["configure_langfuse_env", "tracing_enabled"]
