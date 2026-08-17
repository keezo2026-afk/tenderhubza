.PHONY: setup db migrate geography ingest diagnose schedule notifications schedule-notifications verify-postgres api lint test android-test
setup:
	python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
db:
	docker compose up -d postgres
migrate:
	cd backend && ../.venv/bin/alembic upgrade head
geography:
	cd backend && ../.venv/bin/python -m app.commands.import_geography
ingest:
	cd backend && ../.venv/bin/python -m app.commands.ingest_etenders
diagnose:
	cd backend && ../.venv/bin/python -m app.commands.diagnose_etenders
schedule:
	cd backend && ../.venv/bin/python -m app.commands.schedule_connectors
notifications:
	cd backend && ../.venv/bin/python -m app.commands.run_notification_jobs
schedule-notifications:
	cd backend && ../.venv/bin/python -m app.commands.schedule_notifications
verify-postgres:
	cd backend && ../.venv/bin/python -m app.commands.verify_postgres
api:
	cd backend && ../.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
lint:
	cd backend && ../.venv/bin/ruff format --check app tests && ../.venv/bin/ruff check app tests
test:
	cd backend && ../.venv/bin/pytest
android-test:
	cd android && ./gradlew test
