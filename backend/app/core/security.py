from datetime import datetime, timedelta, timezone
import hashlib
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
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    token = jwt.encode({"sub": subject, "role": role, "exp": expires, "type": "access"}, settings.secret_key, algorithm=ALGORITHM)
    return token, expires

def decode_token(token: str) -> dict:
    return jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])

def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
