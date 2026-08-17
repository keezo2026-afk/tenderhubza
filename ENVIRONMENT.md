# Environment

Copy `.env.example` to `.env`; it is ignored. `SECRET_KEY` is required and has no source-code default.

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | `development`, `test`, or `production` |
| `DATABASE_URL` | SQLAlchemy PostgreSQL URL |
| `SECRET_KEY` | JWT signing secret, at least 32 random characters |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | short access JWT lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | opaque refresh lifetime |
| `PASSWORD_RESET_EXPIRE_MINUTES` | one-time reset lifetime |
| `AUTH_RATE_LIMIT_PER_MINUTE` | per-process endpoint/IP limit |
| `CONNECTOR_TIMEOUT_SECONDS` | eTender HTTP request timeout |
| `CONNECTOR_MAX_ATTEMPTS` | bounded transient attempts |
| `ETENDERS_PAGE_SIZE` | default ingestion page size, maximum 1000 |
| `MAIL_ADAPTER` | `development` returns reset token only in development; configure a production adapter before deployment |
| `CORS_ORIGINS` | comma-separated web origins |
| `LOG_LEVEL` | structured logging level |
| `TENDERHUB_API_URL` | Android Gradle property; base URL ending `/` |

Production must inject all credentials through a secret manager, use database and API TLS, configure restrictive CORS, use a shared rate limiter when scaling beyond one API process, and provide a password-reset delivery adapter. Tokens and passwords must never be placed in logs.

Phase 1A connector settings include `ETENDERS_INITIAL_SYNC_DAYS`, `ETENDERS_OVERLAP_DAYS`, `CONNECTOR_SCHEDULE_ENABLED`, and `CONNECTOR_SCHEDULE_INTERVAL_MINUTES`. Password delivery uses `PUBLIC_APP_URL`; production SMTP uses `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, and `SMTP_STARTTLS`. SMTP credentials are environment-only and must not be committed.

Phase 3 adds `NOTIFICATION_SCHEDULE_ENABLED`, `NOTIFICATION_SCHEDULE_INTERVAL_MINUTES`, `PUSH_PROVIDER`, and `FIREBASE_CREDENTIALS_FILE`. The Firebase credential file is a backend secret and must never be committed. Android Firebase Gradle properties are public client configuration only.
