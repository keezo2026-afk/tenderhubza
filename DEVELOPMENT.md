# Development

## Prerequisites

Python 3.11+, Docker Compose, JDK 17, Android SDK 35 and an API 26+ emulator.

```bash
cp .env.example .env
make setup
make db
make migrate
make geography
make ingest                         # official recent OCDS records
make api                            # http://localhost:8000/api/docs
make test
cd android && ./gradlew testDebugUnitTest assembleDebug
```

The emulator API URL defaults to `http://10.0.2.2:8000/api/v1/`. Override `TENDERHUB_API_URL` in the user Gradle properties for a device or production build. Production must use HTTPS and disable cleartext traffic.

The ingestion command accepts `--date-from`, `--date-to`, `--page`, and `--page-size`. Keep initial imports bounded and inspect `/api/v1/admin/connector-runs` before increasing the window.

## CI

`.circleci/config.yml` defines cached backend and Android jobs. Backend compilation, PostgreSQL migrations, unit/API tests, Android unit tests and debug APK assembly run on every configured CircleCI workflow. Instrumented Compose tests require an emulator and are retained in `androidTest`; the container workflow does not run them.

## Test fixtures

`backend/tests/fixtures/etenders_releases.json` is deterministic OCDS-shaped test input only. It is not loaded by migrations, development startup, the Android app, or production ingestion.
