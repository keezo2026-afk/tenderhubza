# Development

## Prerequisites

Python 3.11+, Docker with Compose, JDK 17, Android Studio (SDK 35), and an API 26+ emulator.

```bash
cp .env.example .env
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
docker compose up -d postgres
cd backend && ../.venv/bin/alembic upgrade head
../.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Tests: `make test`. Android local unit tests: `cd android && ./gradlew test`; instrumented rendering test: `./gradlew connectedAndroidTest` with an emulator. Build APK: `./gradlew assembleDebug`.

For a physical device set `TENDERHUB_API_URL=https://host/api/v1/` in `~/.gradle/gradle.properties`. Cleartext HTTP is enabled only to support local emulator development; use a production network security policy and HTTPS before release.

No admin is seeded. Promote a registered local development user explicitly with SQL: `UPDATE users SET role='ADMIN' WHERE email='you@example.co.za';` Never expose such a workflow in production.
