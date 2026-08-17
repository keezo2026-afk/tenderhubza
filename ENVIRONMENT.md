# Environment

Copy `.env.example` to `.env`; `.env` is ignored.

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | development, test or production label |
| `DATABASE_URL` | SQLAlchemy PostgreSQL URL |
| `SECRET_KEY` | JWT signing secret, minimum 32 characters |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | access-token lifetime |
| `CORS_ORIGINS` | comma-separated allowed web origins |
| `LOG_LEVEL` | structured logging threshold |
| `TENDERHUB_API_URL` | Android Gradle property; API base ending `/` |

Development defaults are intentionally non-secret. Production must inject credentials through the deployment secret manager, rotate signing material, require TLS and not copy development passwords. No API, payment or AI credentials are required in Phase 0.
