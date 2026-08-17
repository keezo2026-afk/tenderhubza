# TenderHub SA

Native Android tender discovery backed by FastAPI, PostgreSQL and a real National Treasury eTender OCDS ingestion path.

## Phase 1 capabilities

- Official OCDS connector with bounded retry and source-specific normalization
- Raw-first, auditable and idempotent ingestion
- Connector-run counters and admin monitoring API
- PostgreSQL generated full-text vector, GIN index, ranking, filtering and server pagination
- Real Home, Search and Tender Details Compose screens
- Refresh-token rotation/reuse detection, standardized errors, reset flow and endpoint rate limits
- Census 2022 district/municipality reference importer with provenance

```bash
cp .env.example .env
make setup db migrate geography
make ingest
make api
```

Open `/api/docs`; run the Android app from `android/` on an API 26+ emulator. See [DEVELOPMENT.md](DEVELOPMENT.md), [ARCHITECTURE.md](ARCHITECTURE.md), [API.md](API.md), [DATABASE.md](DATABASE.md), and [CONNECTORS.md](CONNECTORS.md).

AI/OCR, payments, subscriptions, personalized matching, alerts, broad municipal/SOE connectors, Elasticsearch and analytics remain **NOT IMPLEMENTED**.
