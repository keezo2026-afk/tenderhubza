# Database

PostgreSQL 16 is the production datastore. Alembic revision `0001` creates the Phase 0 schema and seeds only the nine canonical provinces (reference data, not fake tenders).

## Tables

- Identity: `users`, `profiles`, `businesses`, `revoked_tokens`, `password_reset_tokens`
- Geography: `provinces`, `districts`, `municipalities`, `municipal_entities`
- Procurement: `sources`, `tenders`, `raw_ingestions`
- Prepared extensions: `tender_documents`, `tender_requirements`, `tender_amendments`, `tender_source_versions`, `tender_awards`, `tender_analyses`, `tender_matches`

Tender identity is unique on `(source_id, source_reference)`. Filter-oriented columns are indexed. Raw ingestion stores original URL, identifier, JSON payload, ingestion time, connector version, document references and processing states for traceability.

```bash
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/alembic downgrade base # destructive; development only
```

Business preference fields are preparatory only. AI analysis and matching tables establish ownership/audit boundaries; processing is **NOT IMPLEMENTED**.
