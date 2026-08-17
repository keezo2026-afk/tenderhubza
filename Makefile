.PHONY: setup db migrate geography ingest api test android-test
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
api:
	cd backend && ../.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
test:
	cd backend && ../.venv/bin/pytest
android-test:
	cd android && ./gradlew test
