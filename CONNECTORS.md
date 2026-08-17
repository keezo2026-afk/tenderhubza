# Connectors

## National Treasury eTender OCDS

`app/connectors/national/etenders/ETendersConnector` consumes the official National Treasury JSON API at `https://ocds-api.etenders.gov.za/api/OCDSReleases`; its OpenAPI specification is at `https://ocds-api.etenders.gov.za/swagger/index.html`.

Discovery requests a bounded page using `PageNumber`, `PageSize`, `dateFrom`, and `dateTo`. Each discovered OCID is fetched from `/api/OCDSReleases/release/{ocid}` so every stored raw record is reproducible. The connector retries timeouts, transport failures, HTTP 408/429, and 5xx responses with bounded exponential backoff. Permanent 4xx and malformed records are not retried.

Source-specific OCDS names remain inside the connector. It maps the tender, buyer, period, value, contact, classification and document objects into canonical contracts. Missing values remain null. Source timestamps with offsets are parsed before dates and South African closing times are retained as source-local clock values.

Run a bounded recent-data import:

```bash
make ingest
# or
cd backend
../.venv/bin/python -m app.commands.ingest_etenders \
  --date-from 2026-08-15 --date-to 2026-08-17 --page-size 100
```

The default window is seven days and default page size is configurable. Schedule this command externally as one isolated job; Phase 1 intentionally avoids introducing a queue solely for one connector.

## Raw-first lifecycle

```text
discover -> fetch -> INSERT raw_ingestions + COMMIT
         -> parse -> normalize -> validate
         -> find (source_id, source_reference)
         -> insert / payload-hash skip / update
         -> tender_source_versions + documents -> commit
```

Raw durability occurs before parsing. Every changed canonical record has a source-version row pointing to the exact raw representation and a field-level `change_summary`. Identical payloads create an audit raw record but no duplicate canonical tender/version. One item failure updates that raw record and continues the run.

Document metadata and source URLs are stored without eagerly downloading large files. `download_documents()` is the later download boundary.
