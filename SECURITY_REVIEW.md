# Phase 1A Security Review

Reviewed on 2026-08-17.

## Verified controls

- No production credentials, private keys or provider tokens are tracked. `SECRET_KEY` is required from environment configuration.
- Passwords are accepted only in validated request bodies, hashed with Argon2 and never logged.
- Access, refresh and reset token values are not logged. Refresh/reset tokens are persisted only as SHA-256 digests; Android tokens use encrypted preferences.
- Refresh rotation detects reuse and revokes the token family. Password reset revokes active refresh sessions.
- SQLAlchemy expressions and bound SQL parameters are used for user input; no user input is interpolated into SQL.
- FastAPI/Pydantic validates public request shapes and limits page/query sizes.
- All `/admin` routes, including data quality and connector monitoring, use `require_admin`.
- The connector's API host is code/configuration-owned, not supplied by public requests. OCDS document URLs are treated as inert metadata, restricted to valid HTTPS references, and are never downloaded or executed server-side.
- Android opens original/document URLs using the external URI handler and states that TenderHub is not the issuing authority.
- Android release builds disallow cleartext traffic; debug permits local emulator HTTP only.
- Public errors omit stack traces and secrets.

## Open findings

- The in-memory rate limiter is **NOT SAFE FOR HORIZONTAL SCALING**. Use one API process until a shared implementation is authorized.
- SMTP transport and certificate behavior must be validated in the deployment environment. Provider credentials must remain in its secret manager.
- Android uses an alpha/deprecated encrypted-preferences dependency inherited from Phase 0; migration to the current Android credential guidance should be planned after the verified APK baseline.
- A production penetration test, dependency vulnerability scan, Android signing configuration and TLS termination review have not been performed in this sandbox.
