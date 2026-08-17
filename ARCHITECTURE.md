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
