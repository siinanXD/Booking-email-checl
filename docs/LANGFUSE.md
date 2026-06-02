# Langfuse-Observability

Das Projekt nutzt **Langfuse SDK 2.x** (`langfuse==2.60.10`) bewusst ohne
automatischen Rohprompt-Capture. Mailinhalte können PII enthalten und werden als
nicht vertrauenswürdige Daten behandelt.

## Aktivierung

In `.env` (wie bisher):

```env
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com
```

`APP_ENV=test` schaltet Tracing aus (PyTest).

## Was passiert im Code

| Langfuse-Funktion | Dieses Repo |
|-------------------|-------------|
| `@observe` | `capture_input=False`, `capture_output=False` auf Workflow + classify/extract/draft/embed |
| Trace-Session | `langfuse_context.update_current_trace(session_id=correlation_id)` |
| Trace-Metadaten | Nur maskierte IDs und technische Felder |
| Tags nach Klassifikation | `tags=[intent.value]` auf dem Trace |

- **`LLM_MODE=mock`:** Spans/Generations über `@observe`, **keine** OpenAI-Kosten; Modellname aus `.env` nur in Metadaten.
- **`LLM_MODE=live`:** Chat-/Embedding-Aufrufe laufen über das OpenAI SDK; Langfuse sieht nur explizit gesetzte, PII-arme Trace-Daten.

## Sessions in der UI

Alle Schritte einer Mail teilen `session_id = correlation_id` (Mail-Thread). In Langfuse unter **Sessions** gruppieren.

## Embeddings

`IndexingService` erfasst keine Embedding-Rohtexte in Langfuse. Modellname und
Kosten können über explizite Metadaten/Cost-Tracking ergänzt werden, ohne den
Mailinhalt zu senden.
