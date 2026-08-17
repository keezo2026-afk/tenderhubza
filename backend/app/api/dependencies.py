from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ApiError
from app.core.security import decode_token, token_digest
from app.models import RevokedToken, User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise ApiError(401, "UNAUTHENTICATED", "Authentication required")
    try:
        payload = decode_token(credentials.credentials)
    except InvalidTokenError:
        raise ApiError(401, "INVALID_TOKEN", "Invalid or expired token")
    if payload.get("type") != "access" or db.get(
        RevokedToken, token_digest(credentials.credentials)
    ):
        raise ApiError(401, "INVALID_TOKEN", "Invalid or revoked token")
    user = db.get(User, payload.get("sub"))
    if not user or user.status != "ACTIVE":
        raise ApiError(401, "INVALID_USER", "User is unavailable")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "ADMIN":
        raise ApiError(403, "FORBIDDEN", "Admin role required")
    return user
