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

Password-reset requests always return the same generic message. Only in `ENVIRONMENT=development`, with the development adapter and explicit `EXPOSE_DEVELOPMENT_RESET_TOKEN=true`, can the one-time token be returned for local Android testing. Configuration rejects that flag in production. `MAIL_ADAPTER=smtp` uses environment-configured SMTP behind `EmailProvider`; auth business logic has no vendor dependency.

## Phase 2 personal discovery

Authenticated saved-tender endpoints:

- `POST /tenders/{id}/save`
- `DELETE /tenders/{id}/save`
- `GET /tenders/{id}/saved`
- `POST /users/me/saved-tender-status` (batch, maximum 100 IDs)
- `GET /users/me/saved-tenders?page=&page_size=`

Authenticated saved-search CRUD:

- `POST /searches`
- `GET /searches?page=&page_size=`
- `GET /searches/{id}`
- `PUT /searches/{id}`
- `DELETE /searches/{id}`

Profile:

- `GET /users/me/profile`
- `PUT /users/me/profile`

All ownership comes from the access token. Client-supplied user IDs are never accepted. Duplicate saves are idempotent and database-constrained.

## Phase 3 notifications

Authenticated endpoints:

- `GET|PUT /users/me/notification-preferences`
- `GET /notifications`, `GET /notifications/unread-count`
- `POST /notifications/{id}/read`, `POST /notifications/read-all`
- `POST|DELETE /devices/push-token`
- `PUT /tenders/{id}/reminders`

Notification and preference queries are always scoped to the access-token user. There is intentionally no device-token listing endpoint. Admin data quality exposes only aggregate notification/delivery counts.

## Phase 3.5 delivery semantics

Push channel delivery is expanded into `notification_device_deliveries`. Each device independently transitions through `PENDING`, `SUBMITTED`, `FAILED` or `SKIPPED`; `DELIVERED` is reserved for a future provider receipt. Permanently invalid tokens are deactivated. Retrying a parent delivery skips devices already submitted.

## Phase 4 admin source operations

Admin-only: `GET/POST /admin/sources`, `GET/PUT /admin/sources/{id}`, `GET /admin/sources/{id}/runs`, `GET /admin/sources/{id}/health`, `GET /admin/source-coverage`, and existing `/admin/connector-runs`. Creation always starts in DISCOVERED/REVIEW; activation requires prior approval. URLs must be public HTTPS and do not directly trigger server requests.
