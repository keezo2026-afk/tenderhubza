# Connector and ingestion contracts

Each source gets one package under `app/connectors/<source-type>/<source-name>/`; shared scraping logic may be composed but source behavior must remain isolated. Implement `TenderConnector`:

1. `discover()` finds stable source identifiers/URLs.
2. `fetch()` captures an immutable `RawPayload`.
3. `parse()` extracts source fields without canonical assumptions.
4. `normalize()` maps into `NormalizedTender`.
5. `download_documents()` returns document references.

The pipeline is discovery → raw preservation → parsing → normalization → validation → deduplication/persistence → index adapter. Persist raw data before transformations in production. Connector runs should be separate queue jobs with timeout/retry/circuit-breaker policies. Never let one source's exception stop other sources.

Live National Treasury, eThekwini and Eskom implementations are **NOT IMPLEMENTED**; their directories reserve the intended isolation layout. Scheduler, downloader and index adapters are also **NOT IMPLEMENTED**.
