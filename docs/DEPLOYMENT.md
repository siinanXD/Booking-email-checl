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

## Erst-Import bei neuen Mandanten (Phase 7)

Neue Mandanten importieren beim ersten Sync **nicht** das gesamte Postfach:

| Bereich | Regel |
|---------|-------|
| Ab Registrierung | Alle Mails mit `received_at >= mail_ingest_anchor_at` |
| Vor Registrierung | Maximal **50** neueste Mails davor |
| Alles ältere | Wird nicht importiert |

Der Anker (`mail_ingest_anchor_at`) wird bei `POST /auth/register` gesetzt und ist unveränderlich.
Nach dem ersten vollständigen Sync wird `mail_initial_sync_completed_at` gesetzt — danach normales inkrementelles Polling.

**Konfiguration (`.env`):**
```env
MAIL_INGEST_INITIAL_LOOKBACK=50   # Mails vor Anker (Default: 50)
MAIL_INGEST_INITIAL_FETCH_CAP=120 # Max. Fetch-Obergrenze beim ersten Pull
```

**Migration für Bestandsmandanten** (einmalig nach Deploy):
```bash
python scripts/backfill_mail_ingest_flags.py
```
Setzt `mail_initial_sync_completed_at = now()` für alle aktiven Accounts, damit kein erneuter
„Initial"-Lauf alte Mails abschneidet.

---

## Semantisches Chunking Re-Index (Phase 12)

Nach dem ersten Deploy mit semantischem Chunking müssen bestehende Mails re-indexiert werden,
damit alte `\n\n`-Split-Chunks durch semantische Chunks mit Token-Limit, Overlap und Kontext-Prefix
ersetzt werden.

```bash
# Alle Mandanten re-indexieren
python scripts/reindex_semantic_chunks.py

# Nur einen Mandanten
python scripts/reindex_semantic_chunks.py --account-id <account_id>
```

Das Script löscht vor dem Re-Index alle bestehenden Chunks + Embeddings der jeweiligen Mail
(`correlation_id`) und erstellt neue. Idempotent — kann sicher mehrfach ausgeführt werden.

**Achtung:** Bei großen Postfächern können Embedding-API-Kosten entstehen. Vorher in Staging testen.

---

## Nach Go-Live (einmalig)

1. Atlas-Index anlegen (Schritt 5 in `docs/VERIFICATION.md`)
2. `python scripts/backfill_review_drafts.py` für bestehende Mails ohne Review
3. `python scripts/backfill_mail_ingest_flags.py` für Bestandsmandanten (Phase 7)
4. `python scripts/reindex_semantic_chunks.py` für semantisches Chunking (Phase 12)
5. `python scripts/seed_admin.py` falls noch kein Plattform-Admin
6. Langfuse Live-Smoke: Ingest → Review → Freigabe

## Staging-Checkliste

- `pytest -q` und Frontend `npm test && npm run build`
- `SIMILARITY_USE_ATLAS=true` mit Test-Cluster
- WhatsApp Test-Empfänger (`WHATSAPP_TEST_RECIPIENT`) vor Live-Versand
