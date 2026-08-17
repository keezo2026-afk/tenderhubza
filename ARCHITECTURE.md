# Architecture

```text
National Treasury OCDS API
  -> ETendersConnector (bounded retry/timeout)
  -> raw_ingestions COMMIT
  -> parse / canonical normalize / validate
  -> (source_id, source_reference) + payload hash
  -> tender insert | unchanged skip | changed update + source version
  -> PostgreSQL generated tsvector / GIN
  -> FastAPI filters, ranked search, home and details
  -> Retrofit repository / StateFlow ViewModels / Compose
```

## Backend boundaries

Source assumptions live in `connectors/national/etenders`. `ETendersIngestionService` owns raw-first transaction boundaries, validation, idempotency, documents, source versions and connector counters. A command adapter invokes it so a scheduler or queue can be added without changing connector logic. Search is behind `TenderSearch`; production uses PostgreSQL web-search queries and SQLite has a deterministic test-only fallback.

FastAPI routers remain separated by auth, users, tenders, geography, sources and admin. Error handlers enforce one public envelope. Passwords use Argon2; access JWTs are short-lived; opaque refresh tokens rotate by family with reuse detection.

## Android

Compose events enter feature ViewModels and immutable `StateFlow` states. `NetworkTenderRepository` is the API abstraction. Home, search and details render only API records with loading, empty, error and retry states. Search is server paginated. OkHttp's authenticator rotates expired tokens once, retries the request, and emits session invalidation on failure. Both tokens use encrypted preferences.

The public details contract includes normalized fields, source attribution, ingestion timestamp and source documents, but never raw payloads.

## Phase 1A operational controls

Incremental ingestion uses a successful-run high-water date with a configurable overlap. PostgreSQL advisory locking guarantees one active eTender run across scheduler and cron processes. Watermark advancement is in the final successful transaction only. The scheduler handles SIGTERM/SIGINT and waits with an interruptible interval.

`RateLimiter` is a replaceable protocol. Its current implementation is explicitly **NOT SAFE FOR HORIZONTAL SCALING**; deploy one API process or add a shared implementation in a later authorized phase.

Password delivery uses `EmailProvider` with development and SMTP implementations. External OCDS document references are accepted only as valid HTTPS URLs, stored as inert metadata and opened by Android's external URI handler; the backend does not download or execute them.

## Phase 2 personal state

`SavedRepository` is the single Android save-state authority. It batches server state for visible tender IDs and changes its `StateFlow` only after save/unsave API confirmation, keeping Home, Search, Saved and Details consistent. Saved resources remain server-side across logout, restart and device changes.

Saved searches use structured backend validation and reconstruct `TenderFilters` in the retained Search ViewModel. Recent keyword history is device-local, capped at ten and never sent to the backend except when the user executes that search.

## Phase 3 event pipeline

```text
canonical tender insert/update -> deterministic matcher -> notification row
                                                    -> channel delivery rows
hourly reminder job --------------------------------^             |
                                                                  -> Android/API history
```

Creation and delivery are separate and retry-safe. Unique event keys deduplicate saved-search matches, each deadline window and each source version. Matching is deterministic against canonical fields and database-backed saved-search batches—no AI, vectors or suitability claim. Meaningful update fields exclude checksums and ingestion metadata.

Quiet hours defer PUSH/EMAIL via `available_at`; in-app history remains available. High-priority day-of-closing reminders bypass quiet deferral. The same advisory lock pattern prevents overlapping notification batches.

## Phase 3.5 hardening

All connectors now feed the generic `IngestionEngine`; raw durability, validation, canonical identity, geography resolution, idempotency, versions, documents, duplicate candidates, indexing hooks, notifications and run accounting no longer live in the eTender adapter. `IngestionCoordinator` isolates connector-level failures while the engine isolates item failures.

`GeographyResolver` performs code, exact, normalized and alias matching, validates province/district/municipality relationships and records unresolved/conflicting source values. It never guesses an ambiguous municipality.

Push is data-only: Firebase sends title/body/type/IDs as data, `FirebaseMessagingService` always owns notification construction, and one deep-link path is used for foreground, background and terminated process startup. Delivery tracking is per device. Provider acceptance is `SUBMITTED`; `DELIVERED` is reserved for an external receipt.

SQLAlchemy models are split into `users`, `auth`, `geography`, `sources`, `tenders`, `ingestion`, `saved`, and `notifications`; compatibility exports preserve existing imports and table identity. See [TENDER_IDENTITY.md](TENDER_IDENTITY.md) and [MIGRATIONS.md](MIGRATIONS.md).

## Phase 4 source expansion

Source registry, discovery provenance, connector registration, municipal coverage and connector health are distinct domains. `ConnectorRegistry` maps server-controlled implementation slugs to connector classes. New connectors feed the existing generic ingestion engine and therefore search/notifications without Android changes. Zero results are recorded separately from failure; an unexpected zero after a productive run is a warning and never deletes historical tenders.
