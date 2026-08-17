# Tender Identity and Provenance

## Canonical identity

A canonical TenderHub tender is identified internally by `tenders.id`. Within one registered source, the deterministic natural identity is the unique pair:

```text
(source_id, source_reference)
```

`source_reference` is the source's stable contracting-process identity. For National Treasury OCDS this is the OCID. Connectors must not use a release timestamp or mutable title as this field.

## Identifier meanings

| Field | Meaning | Stability |
|---|---|---|
| `tenders.id` | TenderHub canonical database identity | Permanent |
| `source_id` | Registry source that owns this canonical representation | Permanent |
| `source_reference` | Stable source process/record identity used for idempotency | Stable within source |
| `reference_number` | Buyer-facing bid/reference number shown to users | Source-controlled; may be absent or reused |
| `ocds_identifier` | Explicit OCDS contracting process ID for provenance/querying | Stable for OCDS publishers |
| `source_release_id` | Latest source event/release identifier | Changes as releases are published |
| `raw_ingestions.id` | One immutable fetched source representation | One per fetch attempt that reached raw persistence |
| `tender_source_versions.id` | Link from a canonical state transition to its raw representation | One per insert/material update |

## Provenance graph

```text
Canonical Tender
  ├── Source registry record
  ├── Raw ingestion(s)
  ├── Source version(s)
  │     └── field-level change summary
  ├── Document references
  ├── Amendment/award extension tables
  └── Non-destructive duplicate candidates
```

A source release updates the canonical tender in place but never replaces the raw payload or previous source version. Technical-only payload differences remain auditable and must not be confused with user-meaningful amendments.

## Future connector requirements

Each connector must provide a stable `source_reference`; it should additionally provide source release IDs, public reference numbers and source-standard identifiers when available. Where no stable identifier exists, a connector-specific deterministic strategy must be documented and versioned before production enablement.

Cross-source records remain separate canonical tenders. `tender_duplicate_candidates` records confidence, method and signals for later human/data-quality decisions; the platform does not auto-merge them.
