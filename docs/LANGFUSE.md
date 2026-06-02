# Langfuse-Observability

Das Projekt folgt dem Muster aus
[llm_observation.py (Gist)](https://gist.github.com/Chafficui/d6313f4845048b2d9c45fdec5bf7f735),
angepasst an **Langfuse SDK 2.x** (`langfuse>=2.50,<3`).

## Aktivierung

In `.env` (wie bisher):

```env
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com
```

`APP_ENV=test` schaltet Tracing aus (PyTest).

## Was passiert im Code

| Gist (v3-Stil) | Dieses Repo (v2) |
|----------------|------------------|
| `from langfuse.openai import openai` | `OpenAI` / `EmbeddingClient` aus `langfuse.openai` bei `LLM_MODE=live` |
| `@observe` | `langfuse.decorators.observe` auf Workflow + classify/extract/draft |
| `langfuse.update_current_trace(session_id=...)` | `langfuse_context.update_current_trace(session_id=correlation_id)` |
| Tags nach Klassifikation | `tags=[intent.value]` auf dem Trace |

- **`LLM_MODE=mock`:** Spans/Generations über `@observe`, **keine** OpenAI-Kosten; Modellname aus `.env` nur in Metadaten.
- **`LLM_MODE=live`:** Jeder Chat-/Embedding-Aufruf erscheint in Langfuse mit Tokens und Modell (vom SDK erkannt).

## Sessions in der UI

Alle Schritte einer Mail teilen `session_id = correlation_id` (Mail-Thread). In Langfuse unter **Sessions** gruppieren.

## Embeddings

`IndexingService` nutzt bei Live+Tracing ebenfalls `langfuse.openai.OpenAI` → Generationen für `text-embedding-3-small` sichtbar.
