# Gemini (Phase C — Workflow-Sandbox)

Multimodal-Extraktion für **mandantenspezifische Workflows** über Google Gemini.
Die Haupt-Pipeline (Booking-Klassifikation) bleibt bei OpenAI.

## API-Key

1. [Google AI Studio](https://aistudio.google.com/apikey) → API-Key erstellen
2. In `.env` eintragen:

```env
GEMINI_API_KEY=...
GEMINI_MODEL_EXTRACT=gemini-2.0-flash
```

3. Backend neu starten

Status im Dashboard: Workflows → Hinweis verschwindet, wenn `GET /api/workflows/gemini-status` `available: true` meldet.

## Was funktioniert

| Funktion | Gemini |
|----------|--------|
| **KI-Assistent: Vorschlag aus Screenshot/PDF** (`POST /api/workflows/suggest` + `attachments`) | Ja |
| Workflow Preview mit Bild/PDF-Upload | Ja |
| Test-Suite mit gespeicherten Test-Anhängen | Ja |
| Live-Mail mit echten Anhängen | Nein (spätere Phase) |
| Langfuse-Tracing für Gemini | Nein (Phase C) |

Beim Anlegen: Beispiel-Screenshot hochladen → Felder, `match_rules`, Test-Mail
(mit Anhang) und Multimodal-Prompts werden vorgeschlagen. Routing auf echte Mails
nutzt die abgeleiteten Keywords/Domains + Klassifikations-Prompt (Text).

## Limits

- MIME: `image/jpeg`, `image/png`, `image/webp`, `application/pdf`
- Max. 4 MB pro Datei, max. 5 Dateien pro Request

## Dev ohne Google-Kosten

`LLM_MODE=mock` nutzt `MockGemini` mit deterministischen JSON-Antworten.
