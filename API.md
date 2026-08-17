# REST API

Base path `/api/v1`; OpenAPI UI `/api/docs`. Errors always use:

```json
{"error":{"code":"VALIDATION_ERROR","message":"Invalid request","details":{}}}
```

## Authentication

- `POST /auth/register`
- `POST /auth/login` — access and opaque refresh token
- `POST /auth/refresh` — rotates refresh token; reuse revokes its family
- `POST /auth/logout` — revokes access token and optional refresh family
- `POST /auth/password-reset/request`
- `POST /auth/password-reset/confirm`
- `GET /users/me`

Access tokens are short-lived JWTs. Refresh/reset tokens are stored only as SHA-256 digests. In development, the reset request response includes `development_token`; production never returns it and requires a configured delivery adapter. Authentication endpoints have configurable per-process rate limits. A shared limiter is required before horizontal API scaling.

## Tender discovery

`GET /tenders` supports `q`, `page`, `page_size`, `province_id`, `district_id`, `municipality_id`, `category`, `tender_type`, `status`, `closing_from`, `closing_to`, `issue_from`, `issue_to`, `min_value`, `max_value`, `organisation`, and `sort` (`relevance`, `newest`, `closing_soon`). Pages include `total_pages`. Without an explicit status, closed dates and non-open opportunities are excluded.

- `GET /tenders/home` — deterministic latest, closing-soon and recently-added sections
- `GET /tenders/{id}` — canonical fields, source attribution and document references
- `GET /sources`
- `GET /provinces`
- `GET /municipalities?province_id=`
- `GET /health`

Raw payloads and payload hashes are never exposed publicly.

## Admin

Admin bearer token required:

- `POST /sources`
- `GET /admin/connector-runs`
- `GET /admin/sources/monitoring`
- `GET /admin/health`

## Phase 1A additions

- `GET /districts?province_id=` provides backend-owned district reference data.
- `GET /admin/data-quality` reports source health, tender ingestion windows, 30-day processing totals, duplicate candidates and discovered documents.

Password-reset requests always return the same generic message. In development only, the development adapter can return the one-time token to support local Android testing. `MAIL_ADAPTER=smtp` uses environment-configured SMTP behind `EmailProvider`; auth business logic has no vendor dependency.
