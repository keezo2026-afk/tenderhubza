# Architecture

## Runtime

```text
Android (Compose/UDF) -> HTTPS REST /api/v1 -> FastAPI services -> SQLAlchemy -> PostgreSQL
                                                   |
Source -> isolated Connector -> raw_ingestions -> normalize/validate/dedupe -> tenders -> future index
Document URL -> future downloader -> future object storage -> future processors / AI
```

The Android application is independent of persistence. UI events enter `AuthViewModel`; immutable `StateFlow<AuthState>` drives rendering. `AuthRepository` owns network/session behavior, Retrofit defines contracts, and an OkHttp interceptor supplies bearer tokens from `EncryptedSharedPreferences`.

Backend routers separate auth, users, tenders, sources, geography and admin boundaries. Dependency injection owns database sessions and role checks. Configuration comes from environment variables. JSON structured request/error logging is enabled.

## Security

Passwords use Argon2 via `pwdlib`; plaintext passwords are never persisted or returned. JWT access tokens expire and logout stores a SHA-256 token digest until expiry. Admin routes enforce the `ADMIN` role. In production use HTTPS, a generated secret, restrictive CORS, secret management and database TLS.

## Extension points

`TenderConnector` isolates each source with `discover`, `fetch`, `parse`, `normalize`, and `download_documents`. `IngestionPipeline` returns source/item failures instead of crashing the whole run. Future queue, scheduler, object-store and search-index adapters belong behind these boundaries. No live connector or worker scheduler is enabled in Phase 0.
