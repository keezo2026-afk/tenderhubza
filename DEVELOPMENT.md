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

## Phase 1A acceptance commands

```bash
docker compose up -d postgres
make migrate
make geography
make verify-postgres
make diagnose
make ingest
make ingest                  # identical window via explicit date args for repeat proof
```

For scheduled execution set `CONNECTOR_SCHEDULE_ENABLED=true` and run `make schedule` under a process supervisor. For cron, leave the embedded scheduler disabled and invoke `make ingest`; the advisory lock prevents overlap.

If eTender discovery fails, capture the UTC timestamp, `make diagnose` JSON and connector run ID. DNS success plus TCP success plus TLS EOF indicates remote/network-path TLS closure—not an HTTP API response. Do not disable verification.

Android validation requires JDK 17, Android SDK 35 and Gradle wrapper access:

```bash
cd android
./gradlew testDebugUnitTest assembleDebug
# emulator attached:
./gradlew connectedDebugAndroidTest
```

Expected APK: `android/app/build/outputs/apk/debug/app-debug.apk`.

## Phase 2 verification

Migration `0004` creates saved tenders/searches. Backend tests exercise duplicate save, unsave, pagination, unauthenticated access, cross-user isolation, saved-search CRUD and profile updates.

Android tests for saved rendering, empty state, filters and local history are under `androidTest`/`test`. JDK/SDK availability is still required to execute them and build the APK.
