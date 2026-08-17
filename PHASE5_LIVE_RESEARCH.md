# Phase 5 Live Source Research — 2026-08-17

Research used official pages through the validation fetch channel. The backend execution network itself closes TLS to all tested hosts, so no connector could complete a live run. No TLS bypass was used.

| Source | Evidence | Technology/data | Decision |
|---|---|---|---|
| KZN Provincial Treasury | Configured `/Pages/Tenders.aspx` redirects to official SharePoint Page Not Found | SharePoint site; tender location not established | SOURCE_NOT_FOUND |
| eThekwini | Official procurement page returned 52 current tenders with references, closing timestamps, contacts and HTTPS PDF/DOC/XLSX links | Server-rendered structured HTML/CMS; public documents; page appears bounded by year/page | LIVE_CONNECTOR_FEASIBLE, execution-network BLOCKED |
| Msunduzi | Configured HTTPS tender page returned HTTP 500. Search evidence finds official tender notices/opening registers, but links are HTTP/PDF and many documents refer bidders to National Treasury | Document-oriented municipal CMS; current canonical HTTPS listing requires manual verification | REQUIRES_MANUAL_CONFIGURATION |
| Eskom | Official bulletin and bounded `pageSize/pageNumber` returned structured listings. Detail page returned ID, enquiry number, dates, contract type, scope and `/webapi/api/Files/GetFile` document links | Server-rendered application backed by official web API; pagination and public HTTPS documents observed | LIVE_CONNECTOR_FEASIBLE, execution-network BLOCKED |
| SANRAL | Official tender URL redirected to SANRAL user login/registration | Authenticated portal | ACCESS_RESTRICTED |

## Shared-platform finding

No evidence proves that eThekwini, Msunduzi, Eskom, SANRAL or KZN Treasury share a procurement platform. eThekwini exposes a municipal CMS/JDE-related workflow, Msunduzi appears document-oriented, Eskom has its own web API application, KZN uses SharePoint, and SANRAL requires its own account. No shared connector is justified yet.

## Security/access

CAPTCHA or rate-limit behavior could not be tested because bounded backend TLS failed before HTTP. SANRAL authentication was not bypassed. Msunduzi HTTP document links were not used because Phase 5 requires HTTPS. No live source data was inserted.

## Connector implementation status

Production connector classes now exist for eThekwini and Eskom and use only the common `IngestionEngine`. Both are `FIXTURE_VERIFIED` against source-structure fixtures derived from observed official fields. Backend live execution remains blocked at TLS before HTTP, so neither is `LIVE_VERIFIED` and neither source is activated.
