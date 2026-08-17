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
