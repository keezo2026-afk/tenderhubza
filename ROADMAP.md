# Roadmap

## Phase 0 (this repository)

Production-shaped Android/API/database foundation, authentication, canonical tender/source/geography schema, admin source boundary, connector and pipeline contracts, tests and documentation.

## Recommended Phase 1

1. Harden common API error envelopes, refresh-token rotation, password-reset token/email flow and rate limiting.
2. Implement one audited National Treasury connector end-to-end with raw-first persistence, idempotent deduplication, retries and metrics.
3. Add PostgreSQL full-text search and tender filter API; integrate real Home/Search Android repositories and paging.
4. Import authoritative province/district/municipality reference data with provenance/versioning.
5. Add queue/scheduler runtime and connector-run administration/health records.
6. Add CI Android build with SDK caching and PostgreSQL migration integration tests.

AI, matching, subscriptions/payments, OCR, broad source coverage and sophisticated notification delivery remain later phases and are **NOT IMPLEMENTED**.
