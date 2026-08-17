import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()
ALGORITHM = "HS256"


def hash_password(value: str) -> str:
    return password_hash.hash(value)


def verify_password(value: str, encoded: str) -> bool:
    return password_hash.verify(value, encoded)


def create_access_token(subject: str, role: str) -> tuple[str, datetime]:
    s = get_settings()
    expires = datetime.now(UTC) + timedelta(minutes=s.access_token_expire_minutes)
    return jwt.encode(
        {"sub": subject, "role": role, "exp": expires, "type": "access"},
        s.secret_key,
        algorithm=ALGORITHM,
    ), expires


def create_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def decode_token(token: str) -> dict:
    return jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
