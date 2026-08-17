# TenderHub SA

Phase 0 foundation for a native Android South African tender discovery platform backed by a versioned REST API and PostgreSQL.

## Repository

- `android/` — Kotlin, Jetpack Compose, Navigation, StateFlow, Retrofit and encrypted token storage.
- `backend/` — FastAPI, SQLAlchemy, Alembic, JWT authentication and connector/ingestion contracts.
- `docker-compose.yml` — PostgreSQL 16 development service.
- Documentation: [architecture](ARCHITECTURE.md), [API](API.md), [database](DATABASE.md), [connectors](CONNECTORS.md), [development](DEVELOPMENT.md), [environment](ENVIRONMENT.md), [roadmap](ROADMAP.md).

## Quick start

```bash
cp .env.example .env
make setup
make db
make migrate
make api
# separate shell
make test
```

Open API documentation at `http://localhost:8000/api/docs`. Open `android/` in Android Studio and run an API 26+ emulator; its development URL defaults to `http://10.0.2.2:8000/api/v1/`.

Phase 0 deliberately does **not** implement production tender connectors, search ranking, AI, subscriptions, payments, reset-email delivery, or notifications. Placeholders say **NOT IMPLEMENTED** rather than simulating those capabilities.
