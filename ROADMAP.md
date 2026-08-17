# Roadmap

## Phase 1

National Treasury OCDS connector, raw-first ingestion, idempotency/versioning, run monitoring, PostgreSQL search, reference geography, hardened authentication, and API-backed Android tender screens.

## Recommended Phase 2

1. Deploy and schedule the connector with shared rate limiting, run alerts and operational metrics.
2. Add incremental high-water marks and backfill orchestration across the complete OCDS history.
3. Improve source-to-authoritative geography reconciliation and category codelists.
4. Add saved tenders/searches and deterministic closing reminders.
5. Implement secure production reset-email delivery and refresh-session management UI.
6. Add a second source connector only after eTender quality/run SLAs are measured.
7. Introduce document download/object storage with malware and size controls—without AI analysis yet.

AI Tender Reader, OCR/LLM analysis, matching, subscriptions, payments, semantic search and Elasticsearch are **NOT IMPLEMENTED**.

## Phase 1A acceptance gate

No later product phase should begin until a PostgreSQL 16 environment has produced a successful real eTender run, identical repeat, GIN search evidence, passing Android APK build and passing CI. External connectivity or unavailable build infrastructure must remain a reported blocker rather than being replaced with fixtures.

## Recommended Phase 3 (requires separate authorization)

After Phase 1A live acceptance, focus on saved-tender closing reminders and notification preference infrastructure, production observability, and business-profile completion. Do not begin AI, payments or alerts until separately authorized.

## Recommended Phase 4 (separate authorization required)

Complete real PostgreSQL/FCM/device acceptance first, then consider notification delivery receipts/analytics, richer per-search schedules and production operational tooling. AI, payments and business matching remain out of scope until explicitly authorized.
