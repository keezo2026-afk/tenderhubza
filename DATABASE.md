# Database

PostgreSQL 16 is the production datastore. Apply Alembic revisions with `make migrate`.

## Phase 1 changes (`0002`)

- `connector_runs`: run status, timing, counters and isolated failure summary.
- `tender_duplicate_candidates`: non-destructive cross-source candidate pairs for later review.
- `refresh_tokens`: hashed rotating tokens, family, replacement, use and revocation state.
- `geography_datasets`: source URL, version and import timestamp.
- `raw_ingestions`: request URL/status/content type/response time, checksum, OCDS and release IDs.
- `tenders`: checksum, release/OCDS identifiers, ingestion timestamp and nullable geographic foreign keys.
- `tender_source_versions.change_summary`: field-level change audit linked to exact raw input.
- `districts.dataset_id` and `municipalities.dataset_id`: provenance link.
- PostgreSQL generated `search_vector` and GIN index, plus current-opportunity sort index.
- Idempotent National Treasury eTender OCDS source bootstrap.

Canonical uniqueness remains `(source_id, source_reference)`. Identical checksums skip canonical writes; changed checksums update in place and append a source version. Original payloads are never deleted by ingestion.

## Geography

`make geography` imports committed, deterministic Census 2022 administrative reference extracts: 9 provinces already seeded in Phase 0, 52 district/metro geography rows and 213 local/metro municipalities. The original source is Stats SA’s *Census 2022 Provinces at a Glance*. The committed compact CSVs are independently processed extracts from `afrith/census-2022-muni-stats` (Tabula plus manual cleanup), and Stats SA is acknowledged as the original source. The importer records provenance and is idempotent. Geographic links on tenders are nullable because national, provincial and public-entity opportunities need not map to municipalities.

The compact CSV extracts contain only codes, hierarchy, names and classification—not census indicators.

## Phase 1A migration (`0003`)

`connector_states` stores the source high-water date and successful run reference. It is deliberately separate from run history. A failed or partial run leaves this row unchanged.

After PostgreSQL migration and geography import, run `make verify-postgres`. The command refuses SQLite and reports PostgreSQL version, required tables, `search_vector` type, GIN index definition, registered source, geography counts, search timing and `EXPLAIN (ANALYZE, BUFFERS)` output.

## Phase 2 migration (`0004`)

- `saved_tenders`: server-persisted user/tender association with cascade deletion, indexed `user_id` and `tender_id`, and unique `(user_id, tender_id)`.
- `saved_searches`: user-owned name, query, structured JSON filters, sort, timestamps, and indexed `user_id`. Structured filter validation mirrors the discovery API and is suitable for future notification matching without implementing notifications now.

## Phase 3 migration (`0006`)

- `notification_preferences`: one per user, channel/event consent, quiet hours and IANA timezone.
- `notifications`: private user history with type, priority, tender/search links, read state and globally unique deterministic `event_key`.
- `notification_deliveries`: channel attempts, retry count, availability time, honest `PENDING/SUBMITTED/DELIVERED/FAILED/SKIPPED` state and provider ID. `SUBMITTED` means provider acceptance; `DELIVERED` is reserved for a real receipt.
- `device_tokens`: multiple minimal Android registrations per user; tokens are never returned by an API.
- `saved_searches.alerts_enabled` and `saved_tenders.closing_reminders_enabled/reminder_days` support per-resource controls.

## Phase 3.5 migration (`0007`)

This first explicit-policy migration adds geography-resolution audit records, per-device notification deliveries, duplicate-candidate confidence/method/signals, and a PostgreSQL GIN index for saved-search filter candidate narrowing. It converts provider-accepted parent delivery state from `SENT` to `SUBMITTED`. Historical `create_all` coupling is documented in [MIGRATIONS.md](MIGRATIONS.md); all future revisions must use explicit Alembic operations.
