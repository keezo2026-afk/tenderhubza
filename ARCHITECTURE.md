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
