from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token, token_digest
from app.models import RevokedToken, User
bearer=HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials|None=Depends(bearer), db:Session=Depends(get_db))->User:
    if not credentials: raise HTTPException(status_code=401, detail={"code":"UNAUTHENTICATED","message":"Authentication required"})
    try: payload=decode_token(credentials.credentials)
    except InvalidTokenError: raise HTTPException(status_code=401, detail={"code":"INVALID_TOKEN","message":"Invalid or expired token"})
    if db.get(RevokedToken, token_digest(credentials.credentials)): raise HTTPException(status_code=401, detail={"code":"REVOKED_TOKEN","message":"Token has been revoked"})
    user=db.get(User,payload.get("sub"))
    if not user or user.status!="ACTIVE": raise HTTPException(status_code=401, detail={"code":"INVALID_USER","message":"User is unavailable"})
    return user

def require_admin(user:User=Depends(get_current_user))->User:
    if user.role!="ADMIN": raise HTTPException(status_code=403, detail={"code":"FORBIDDEN","message":"Admin role required"})
    return user
