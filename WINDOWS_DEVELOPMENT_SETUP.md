# TenderHub SA — Windows Development and Acceptance Setup

This handoff targets Windows 10/11 with PowerShell 7 or Windows PowerShell 5.1. Run commands from the repository root unless a section says otherwise.

> **Current acceptance status:** Phase 1A live acceptance remains blocked in Arena. eThekwini and Eskom connectors are fixture verified, not live verified. This guide is the procedure for completing external acceptance without weakening TLS.

## 1. Repository-pinned requirements

### Backend

- Python: **3.11 or newer** (the code/lint target is Python 3.11)
- PostgreSQL: **16** (`postgres:16-alpine` in Compose)
- Exact Python packages: `backend/requirements.txt`
- Development tools: `backend/requirements-dev.txt` (includes Ruff 0.12.11)

### Android

- JDK: **17**
- Gradle wrapper: **8.10.2**
- Android Gradle Plugin: **8.7.3**
- Kotlin and Compose compiler plugin: **2.1.0**
- Compile/target SDK: **35**
- Minimum SDK: **26**
- Application ID/namespace: `za.co.tenderhub`
- Firebase Messaging client: **24.1.0**

No Android Studio release or Android Build Tools patch is pinned in the repository. Use a current stable Android Studio that supports AGP 8.7.3, install Android SDK Platform 35 and platform-tools, and let AGP select/download a compatible 35.x build-tools revision. Record the resolved revision from the build rather than inventing one.

## 2. Prerequisites

Install from official vendors:

1. Git for Windows.
2. Python 3.11+ x64; enable the Python launcher (`py`).
3. Docker Desktop with WSL 2 backend and Docker Compose v2.
4. JDK 17 (Temurin/Microsoft/OpenJDK distribution).
5. Current stable Android Studio.
6. In Android Studio SDK Manager:
   - Android SDK Platform 35
   - Android SDK Platform-Tools
   - Android SDK Command-line Tools (latest)
   - Android Emulator
   - One API 35 x86_64/arm64 system image appropriate for the host
7. Optional: OpenSSL for explicit TLS diagnostics. Git for Windows commonly includes it.

Verify in a new PowerShell window:

```powershell
git --version
py -3.11 --version
docker version
docker compose version
java -version
adb version
```

`java -version` must report major version 17.

## 3. Clone and branch

```powershell
git clone https://github.com/keezo2026-afk/tenderhubza.git
Set-Location tenderhubza
git fetch origin arena/01a00f29-tenderhubza
git switch --track origin/arena/01a00f29-tenderhubza
# If the local branch already exists:
# git switch arena/01a00f29-tenderhubza
git log -1 --oneline
```

Expected Phase 5B commit at handoff: `f2be219` or a later authorized remediation commit.

## 4. Backend virtual environment

```powershell
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements-dev.txt
```

Verify:

```powershell
python --version
python -m pytest --version
python -m ruff --version
```

## 5. Environment configuration

```powershell
Copy-Item .env.example .env
```

Generate a development signing secret without putting it in chat or source control:

```powershell
$bytes = New-Object byte[] 48
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$rng.Dispose()
$secret = [Convert]::ToBase64String($bytes)
(Get-Content .env).Replace(
  'SECRET_KEY=replace-with-at-least-32-random-characters',
  "SECRET_KEY=$secret"
) | Set-Content .env
```

Development database URL from `.env.example`:

```text
postgresql+psycopg://tenderhub:tenderhub_dev@localhost:5432/tenderhub
```

Keep `.env` untracked:

```powershell
git check-ignore .env
```

Never commit SMTP, Firebase service-account, API, database-production, or JWT secrets.

## 6. PostgreSQL 16 and migrations

Start the configured service:

```powershell
docker compose up -d postgres
docker compose ps
docker compose logs postgres --tail 50
```

Wait until the health column reports healthy. Then run migrations and reference import:

```powershell
Push-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m alembic current
..\.venv\Scripts\python.exe -m app.commands.import_geography
..\.venv\Scripts\python.exe -m app.commands.verify_postgres
..\.venv\Scripts\python.exe -m app.commands.bootstrap_source_candidates
Pop-Location
```

Expected migration head:

```text
0008
```

`verify_postgres` must report:

- PostgreSQL 16 server version
- no missing required tables
- `search_vector` type `tsvector`
- `ix_tenders_search_vector` GIN definition
- National Treasury source registration
- 9 provinces, 52 district/metro rows and 213 local/metro municipalities
- an `EXPLAIN (ANALYZE, BUFFERS)` plan

Do not count SQLite as production database acceptance.

Useful database checks:

```powershell
docker compose exec postgres psql -U tenderhub -d tenderhub -c "SELECT version();"
docker compose exec postgres psql -U tenderhub -d tenderhub -c "SELECT version_num FROM alembic_version;"
docker compose exec postgres psql -U tenderhub -d tenderhub -c "SELECT indexname,indexdef FROM pg_indexes WHERE indexdef ILIKE '%using gin%';"
```

Reset only a disposable local database:

```powershell
docker compose down -v
docker compose up -d postgres
```

## 7. Backend quality and startup

```powershell
Push-Location backend
..\.venv\Scripts\python.exe -m ruff format --check app tests
..\.venv\Scripts\python.exe -m ruff check app tests
..\.venv\Scripts\python.exe -m compileall -q app
..\.venv\Scripts\python.exe -m pytest -q
Pop-Location
```

Start the API in a dedicated PowerShell window:

```powershell
Set-Location C:\path\to\tenderhubza\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health and OpenAPI:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
Start-Process http://localhost:8000/api/docs
```

Expected health body contains `status: ok`.

## 8. Verified HTTPS connectivity gate

Run this before any live connector. All commands retain normal certificate verification.

```powershell
$hosts = @(
  'www.durban.gov.za',
  'tenderbulletin.eskom.co.za',
  'ocds-api.etenders.gov.za'
)
foreach ($hostName in $hosts) {
  Resolve-DnsName $hostName
  Test-NetConnection $hostName -Port 443
}
```

Verified HTTPS/HTTP checks:

```powershell
curl.exe -Iv --http1.1 --tlsv1.2 https://www.durban.gov.za/pages/business/procurement
curl.exe -Iv --http1.1 --tlsv1.2 "https://tenderbulletin.eskom.co.za/?pageSize=5&pageNumber=1"
curl.exe -Iv --http1.1 --tlsv1.2 "https://ocds-api.etenders.gov.za/api/OCDSReleases?PageNumber=1&PageSize=1"

Invoke-WebRequest https://www.durban.gov.za/pages/business/procurement -Method Head
Invoke-WebRequest "https://tenderbulletin.eskom.co.za/?pageSize=5&pageNumber=1" -Method Head
Invoke-WebRequest "https://ocds-api.etenders.gov.za/api/OCDSReleases?PageNumber=1&PageSize=1" -Method Get
```

If OpenSSL is installed:

```powershell
openssl s_client -connect www.durban.gov.za:443 -servername www.durban.gov.za -tls1_2 -verify_return_error
openssl s_client -connect tenderbulletin.eskom.co.za:443 -servername tenderbulletin.eskom.co.za -tls1_2 -verify_return_error
openssl s_client -connect ocds-api.etenders.gov.za:443 -servername ocds-api.etenders.gov.za -tls1_2 -verify_return_error
```

Stop if TLS does not complete. Do not use `-k`, `verify=False`, HTTP downgrade, custom untrusted CAs, or unapproved proxies.

## 9. Bounded eThekwini live connector acceptance

The repository does not provide a source-specific ingestion service. Use the connector with the common `IngestionEngine` exactly as follows from `backend`:

```powershell
@'
import asyncio
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models import Source
from app.connectors.municipal.ethekwini import EThekwiniConnector
from app.ingestion.engine import IngestionEngine
from app.services.connector_execution import connector_lock

async def main():
    with SessionLocal() as db:
        source = db.scalar(select(Source).where(Source.slug == "ethekwini-municipality"))
        if source is None:
            raise SystemExit("Run import_geography and bootstrap_source_candidates first")
        connector = EThekwiniConnector(limit=25)
        with connector_lock(db, connector.NAME):
            run = await IngestionEngine(db, connector).run(source)
        print({
            "run_id": run.id,
            "status": run.status,
            "discovered": run.records_discovered,
            "fetched": run.records_fetched,
            "parsed": run.records_parsed,
            "normalized": run.records_normalized,
            "inserted": run.records_inserted,
            "updated": run.records_updated,
            "skipped": run.records_skipped,
            "failed": run.records_failed,
            "documents": run.documents_discovered,
        })

asyncio.run(main())
'@ | ..\.venv\Scripts\python.exe -
```

Run the exact command twice. Before/after canonical counts:

```powershell
docker compose exec postgres psql -U tenderhub -d tenderhub -c "SELECT count(*) FROM tenders t JOIN sources s ON s.id=t.source_id WHERE s.slug='ethekwini-municipality';"
docker compose exec postgres psql -U tenderhub -d tenderhub -c "SELECT source_id,source_reference,count(*) FROM tenders GROUP BY source_id,source_reference HAVING count(*)>1;"
```

Expected live acceptance:

- first run: `discovered > 0`, ideally `inserted > 0`
- second identical run: `skipped > 0`
- canonical count difference on repeat: zero
- duplicate query: zero rows

Do not modify an official source to demonstrate updates. Record update/version as `NOT TESTED` unless the source naturally changes.

## 10. Bounded Eskom live connector acceptance

From `backend`:

```powershell
@'
import asyncio
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models import Source
from app.connectors.soe.eskom import EskomConnector
from app.ingestion.engine import IngestionEngine
from app.services.connector_execution import connector_lock

async def main():
    with SessionLocal() as db:
        source = db.scalar(select(Source).where(Source.slug == "eskom-tender-bulletin"))
        if source is None:
            raise SystemExit("Run bootstrap_source_candidates first")
        connector = EskomConnector(page_size=25, page_number=1)
        with connector_lock(db, connector.NAME):
            run = await IngestionEngine(db, connector).run(source)
        print({
            "run_id": run.id,
            "status": run.status,
            "discovered": run.records_discovered,
            "fetched": run.records_fetched,
            "parsed": run.records_parsed,
            "normalized": run.records_normalized,
            "inserted": run.records_inserted,
            "updated": run.records_updated,
            "skipped": run.records_skipped,
            "failed": run.records_failed,
            "documents": run.documents_discovered,
        })

asyncio.run(main())
'@ | ..\.venv\Scripts\python.exe -
```

Run twice and use the same canonical duplicate checks, replacing the source slug with `eskom-tender-bulletin`.

Verify document provenance without downloading files:

```powershell
docker compose exec postgres psql -U tenderhub -d tenderhub -c "SELECT d.name,d.source_url FROM tender_documents d JOIN tenders t ON t.id=d.tender_id JOIN sources s ON s.id=t.source_id WHERE s.slug='eskom-tender-bulletin' LIMIT 25;"
```

All Eskom URLs must use HTTPS and the official Eskom host.

## 11. Search acceptance

Normal API only—there is no source-specific endpoint:

```powershell
$search = Invoke-RestMethod "http://localhost:8000/api/v1/tenders?q=construction&sort=relevance&page=1&page_size=20"
$search.total
$search.items | Select-Object id,title,organisation,reference_number,closing_date

Invoke-RestMethod "http://localhost:8000/api/v1/tenders?organisation=eThekwini%20Metropolitan%20Municipality&sort=closing_soon"
Invoke-RestMethod "http://localhost:8000/api/v1/tenders?organisation=Eskom%20Holdings%20SOC%20Ltd&sort=newest"
```

Reference search:

```powershell
Invoke-RestMethod "http://localhost:8000/api/v1/tenders?q=MWP2759GX"
```

Verify page overlap is empty by comparing IDs from page 1 and page 2.

## 12. Saved-search and notification acceptance

Register/login through `/api/docs` or PowerShell. Example:

```powershell
$body = @{email='acceptance@example.test';password='StrongPass123!';first_name='Acceptance';last_name='User'} | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/api/v1/auth/register -Method Post -ContentType application/json -Body $body
$login = Invoke-RestMethod http://localhost:8000/api/v1/auth/login -Method Post -ContentType application/json -Body (@{email='acceptance@example.test';password='StrongPass123!'} | ConvertTo-Json)
$headers = @{Authorization="Bearer $($login.access_token)"}
```

Create the saved search **before the first live ingestion**:

```powershell
$searchBody = @{
  name='Live connector acceptance'
  query='construction'
  filters=@{}
  sort='relevance'
  alerts_enabled=$true
} | ConvertTo-Json -Depth 5
Invoke-RestMethod http://localhost:8000/api/v1/searches -Method Post -Headers $headers -ContentType application/json -Body $searchBody
```

After ingestion:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/notifications -Headers $headers
Invoke-RestMethod http://localhost:8000/api/v1/notifications/unread-count -Headers $headers
```

Repeat ingestion and confirm no additional event for the same tender/search pair:

```powershell
docker compose exec postgres psql -U tenderhub -d tenderhub -c "SELECT event_key,count(*) FROM notifications GROUP BY event_key HAVING count(*)>1;"
```

Expected: zero rows.

## 13. Health and provenance acceptance

```powershell
docker compose exec postgres psql -U tenderhub -d tenderhub -c "SELECT slug,status,last_attempted_at,last_successful_run,last_failed_run,last_tender_discovered_at,consecutive_failures,last_error_category FROM sources WHERE slug IN ('ethekwini-municipality','eskom-tender-bulletin');"
docker compose exec postgres psql -U tenderhub -d tenderhub -c "SELECT s.slug,r.id,r.connector_name,r.connector_version,r.status,r.records_discovered,r.records_inserted,r.records_updated,r.records_skipped,r.records_failed,r.documents_discovered FROM connector_runs r JOIN sources s ON s.id=r.source_id WHERE s.slug IN ('ethekwini-municipality','eskom-tender-bulletin') ORDER BY r.started_at DESC;"
docker compose exec postgres psql -U tenderhub -d tenderhub -c "SELECT s.slug,count(ri.id) raw_count,count(DISTINCT t.id) tender_count,count(v.id) version_count FROM sources s LEFT JOIN raw_ingestions ri ON ri.source_id=s.id LEFT JOIN tenders t ON t.source_id=s.id LEFT JOIN tender_source_versions v ON v.tender_id=t.id WHERE s.slug IN ('ethekwini-municipality','eskom-tender-bulletin') GROUP BY s.slug;"
```

Health must derive from runs; do not edit timestamps to manufacture `HEALTHY`.

## 14. Android environment

Set persistent Windows variables (adjust the SDK path if Android Studio uses another location):

```powershell
[Environment]::SetEnvironmentVariable('JAVA_HOME','C:\Program Files\Eclipse Adoptium\jdk-17','User')
[Environment]::SetEnvironmentVariable('ANDROID_HOME',"$env:LOCALAPPDATA\Android\Sdk",'User')
```

Open a new terminal:

```powershell
$env:Path += ";$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:ANDROID_HOME\emulator;$env:ANDROID_HOME\cmdline-tools\latest\bin"
java -version
sdkmanager --list_installed
adb version
```

User Gradle properties:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.gradle"
notepad "$env:USERPROFILE\.gradle\gradle.properties"
```

For Android emulator/backend on the same Windows host:

```properties
TENDERHUB_API_URL=http://10.0.2.2:8000/api/v1/
```

For a physical device, use a reachable LAN URL or an approved HTTPS development endpoint; never use `localhost` from the device.

## 15. Android build and tests

```powershell
Set-Location android
.\gradlew.bat --version
.\gradlew.bat testDebugUnitTest
.\gradlew.bat assembleDebug
```

Expected APK:

```text
android\app\build\outputs\apk\debug\app-debug.apk
```

Verify:

```powershell
Test-Path .\app\build\outputs\apk\debug\app-debug.apk
Get-FileHash .\app\build\outputs\apk\debug\app-debug.apk -Algorithm SHA256
apkanalyzer manifest application-id .\app\build\outputs\apk\debug\app-debug.apk
apkanalyzer manifest min-sdk .\app\build\outputs\apk\debug\app-debug.apk
apkanalyzer manifest target-sdk .\app\build\outputs\apk\debug\app-debug.apk
apkanalyzer manifest print .\app\build\outputs\apk\debug\app-debug.apk | Select-String 'tenderhub|MESSAGING_EVENT|POST_NOTIFICATIONS|usesCleartextTraffic'
```

Expected:

- Application ID: `za.co.tenderhub`
- Min SDK: 26
- Target SDK: 35
- Tender and notification deep-link intent filters
- `TenderHubMessagingService`
- `POST_NOTIFICATIONS`
- Debug cleartext allowed for emulator development
- Release cleartext disabled by the manifest placeholder

## 16. Emulator/device tests

Create and boot an API 35 AVD in Android Studio Device Manager, then:

```powershell
adb devices
.\gradlew.bat connectedDebugAndroidTest
```

Install manually if needed:

```powershell
adb install -r .\app\build\outputs\apk\debug\app-debug.apk
adb shell am start -a android.intent.action.VIEW -d "tenderhub://notifications" za.co.tenderhub
adb shell am start -a android.intent.action.VIEW -d "tenderhub://tender/REPLACE_WITH_REAL_TENDER_ID" za.co.tenderhub
```

A missing tender ID must show the application error state, not crash.

## 17. Firebase configuration

### Android public configuration

The application initializes Firebase from public Gradle properties; it does not require committing a service-account key. Add to the user Gradle properties only after creating/authorizing the legitimate Firebase Android app for package `za.co.tenderhub`:

```properties
FIREBASE_API_KEY=<public Android API key>
FIREBASE_APP_ID=<Firebase Android app ID>
FIREBASE_PROJECT_ID=<Firebase project ID>
FIREBASE_SENDER_ID=<messaging sender ID>
```

These values are Firebase client identifiers. Apply appropriate Firebase API-key restrictions in Google Cloud.

### Backend private configuration

Download a service-account credential only through the Firebase/Google Cloud console into a secure path outside the repository. Never commit it.

Set in `.env` using an absolute Windows path:

```text
PUSH_PROVIDER=firebase
FIREBASE_CREDENTIALS_FILE=C:/secure/tenderhub/firebase-service-account.json
```

Confirm `.gitignore` and `git status` before continuing.

### Runtime acceptance

1. Log in on Android.
2. Explain notification benefit and enable push in Notification Settings.
3. Grant Android 13+ permission.
4. Verify `device_tokens` has an active record without printing the token.
5. Create a notification through the normal matcher/reminder path.
6. Run `python -m app.commands.run_notification_jobs`.
7. Test foreground, background and terminated app states.
8. Tap tender notifications and verify Tender Details.
9. Send a payload without `tender_id` and verify Notification Center.
10. Send malformed data and verify no crash.
11. Logout and verify the device registration becomes inactive.

Firebase Admin provider acceptance is `SUBMITTED`, not `DELIVERED`; do not claim delivery receipts that Firebase does not provide.

## 18. CircleCI connection

The repository contains `.circleci/config.yml`, but the project must be connected externally.

1. Sign in to CircleCI with the GitHub organisation account.
2. Install/authorize the official CircleCI GitHub App for this repository.
3. Set up the project using the existing `.circleci/config.yml`; do not generate a replacement config.
4. Configure required secrets in CircleCI project contexts/environment variables, never in YAML.
5. Push or trigger branch `arena/01a00f29-tenderhubza`.
6. Require both backend and Android jobs.

Expected backend job:

- Python environment
- Ruff
- Compilation
- PostgreSQL 16 service
- Alembic head migration
- Geography import
- PostgreSQL verification
- Backend tests

Expected Android job:

- JDK/Android container
- Unit tests
- Debug APK build
- APK artifact retention

Record the actual pipeline URL, commit SHA, job results and artifact URL. No CI result exists until CircleCI reports it.

## 19. Troubleshooting

### PostgreSQL port already in use

```powershell
Get-NetTCPConnection -LocalPort 5432
```

Stop the conflicting local PostgreSQL service or change the Compose host port and `DATABASE_URL` together.

### Docker database not healthy

```powershell
docker compose logs postgres
docker compose exec postgres pg_isready -U tenderhub -d tenderhub
```

### Emulator cannot reach API

- API must bind `0.0.0.0:8000`.
- Emulator uses `10.0.2.2`, not `localhost`.
- Permit inbound TCP 8000 in Windows Firewall for the selected network profile if required.

### Gradle uses the wrong JDK

```powershell
.\gradlew.bat --version
```

Set Android Studio Gradle JDK and `JAVA_HOME` to JDK 17.

### TLS source failure

Capture:

```powershell
Resolve-DnsName <host>
Test-NetConnection <host> -Port 443
curl.exe -Iv --http1.1 --tlsv1.2 https://<host>/...
```

Do not use `curl -k`, `verify=False`, HTTP fallback, or custom untrusted certificates. If a corporate TLS-inspection environment is involved, use only organisation-approved trust configuration and document it separately.

### Connector returns zero

Inspect the connector run, raw ingestion, source health and page manually. Do not delete historical tenders or mark the run failed solely because it returned zero. Investigate `zero_result_anomaly`.

## 20. Acceptance record

For each live connector record:

```text
Timestamp
Git commit
Source URL
DNS/TCP/TLS/HTTP evidence
Run ID
Connector/version
Discovered/fetched/parsed/normalized
Inserted/updated/skipped/failed
Documents
Canonical count before/after repeat
Search query/result
Notification event key/count
Health state
Known source issues
Classification: LIVE VERIFIED / FIXTURE VERIFIED / BLOCKED
```

Do not classify a source as live verified until the backend connector itself completes verified HTTPS discovery and ingestion.
