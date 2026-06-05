# Deployment & Betrieb

## Voraussetzungen

- Python 3.11, Node 20+ für Frontend-Build
- MongoDB Atlas (empfohlen) mit Mandanten-`account_id` auf allen Collections
- Optional: Atlas Vector Search Index `embedding_vector_index` wenn `SIMILARITY_USE_ATLAS=true`

## Umgebungsvariablen (Produktion)

Siehe `.env.example`. Mindestens:

- `MONGODB_URI`, `JWT_SECRET`, `OPENAI_API_KEY`
- `LLM_MODE=live`
- Outlook oder IMAP-Credentials pro Mandant (über UI-Onboarding)
- `WHATSAPP_*` wenn Benachrichtigungen aktiv
- `LANGFUSE_*` für Observability

## Build & Start

```bash
pip install -e ".[dev]"
cd frontend && npm ci && npm run build
# Backend statische Dateien aus frontend/dist servieren (siehe api/app.py)
python -m backend.api.app
```

## Skalierung

- **API:** horizontal skalierbar; gemeinsame MongoDB
- **Mail-Poll:** ein Worker pro Deployment oder dedizierter Job-Container (`MAIL_POLL_RUN_ONCE=1` in Cron)
- **Embeddings:** asynchrones Indexing; Fehler erzeugen Alerts (Webhook)

## Kosten

- Triage-LLM für unbekannte Absender reduziert teure classify/extract-Läufe — siehe `docs/COST_TRIAGE.md`
- Dashboard `/costs` und Admin-Observability für Token-Auswertung
- **Geplant (Roadmap Phase 7):** Neue Mandanten importieren beim ersten Sync nur Mails ab
  Registrierungszeitpunkt plus 50 davor — kein Voll-Import historischer Postfächer.
  Siehe `docs/ROADMAP.md` Phase 7 und Migration `mail_initial_sync_completed_at` für Bestandskunden.

## Nach Go-Live (einmalig)

1. Atlas-Index anlegen (Schritt 5 in `docs/VERIFICATION.md`)
2. `python scripts/backfill_review_drafts.py` für bestehende Mails ohne Review
3. `python scripts/seed_admin.py` falls noch kein Plattform-Admin
4. Langfuse Live-Smoke: Ingest → Review → Freigabe

## Staging-Checkliste

- `pytest -q` und Frontend `npm test && npm run build`
- `SIMILARITY_USE_ATLAS=true` mit Test-Cluster
- WhatsApp Test-Empfänger (`WHATSAPP_TEST_RECIPIENT`) vor Live-Versand
