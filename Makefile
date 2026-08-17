.PHONY: setup db migrate api test android-test
setup:
	python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
db:
	docker compose up -d postgres
migrate:
	cd backend && ../.venv/bin/alembic upgrade head
api:
	cd backend && ../.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
test:
	cd backend && ../.venv/bin/pytest
android-test:
	cd android && ./gradlew test
