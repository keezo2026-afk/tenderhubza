# REST API

Base path: `/api/v1`. Interactive OpenAPI: `/api/docs`. Bearer authentication: `Authorization: Bearer <JWT>`.

| Method | Path | Access | Status |
|---|---|---|---|
| GET | `/health` | Public | Implemented |
| POST | `/auth/register` | Public | Implemented |
| POST | `/auth/login` | Public | Implemented |
| POST | `/auth/logout` | Authenticated | Implemented |
| GET | `/users/me` | Authenticated | Implemented |
| GET | `/tenders` | Public | Implemented, basic pagination/filtering |
| GET | `/tenders/{id}` | Public | Implemented |
| GET | `/sources` | Public | Implemented |
| POST | `/sources` | Admin | Implemented |
| GET | `/provinces` | Public | Implemented |
| GET | `/municipalities?province_id=` | Public | Implemented |
| GET | `/admin/health` | Admin | Implemented foundation |

Admin tender creation exists for ingestion/tests but is hidden from the public OpenAPI while the ingestion write contract stabilizes. Pages return `{items,page,page_size,total}`. Validation uses HTTP 422; authentication 401; authorization 403; conflict 409; missing resource 404. Errors contain a machine code and message under FastAPI's `detail` field for handled API errors. A future exception-normalization pass should make validation and handled/unhandled envelopes completely identical.

Password reset API/email delivery is **NOT IMPLEMENTED**. Search beyond exact Phase 0 filters is **NOT IMPLEMENTED**.
