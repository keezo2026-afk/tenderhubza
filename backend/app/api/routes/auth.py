from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.dependencies import bearer, get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, decode_token, hash_password, token_digest, verify_password
from app.models import Profile, RevokedToken, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.domain import UserOut
router=APIRouter(prefix="/auth",tags=["auth"])
@router.post("/register",response_model=UserOut,status_code=201)
def register(data:RegisterRequest,db:Session=Depends(get_db)):
    email=data.email.lower()
    if db.scalar(select(User).where(User.email==email)): raise HTTPException(409,detail={"code":"EMAIL_EXISTS","message":"An account with this email already exists"})
    user=User(email=email,password_hash=hash_password(data.password),first_name=data.first_name,last_name=data.last_name,phone=data.phone)
    user.profile=Profile(display_name=f"{data.first_name} {data.last_name}",notification_preferences={})
    db.add(user)
    try: db.commit()
    except IntegrityError: db.rollback(); raise HTTPException(409,detail={"code":"EMAIL_EXISTS","message":"An account with this email already exists"})
    db.refresh(user); return user
@router.post("/login",response_model=TokenResponse)
def login(data:LoginRequest,db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==data.email.lower()))
    if not user or not verify_password(data.password,user.password_hash): raise HTTPException(401,detail={"code":"INVALID_CREDENTIALS","message":"Email or password is incorrect"})
    if user.status!="ACTIVE": raise HTTPException(403,detail={"code":"ACCOUNT_DISABLED","message":"Account is not active"})
    token,expires=create_access_token(user.id,user.role); return TokenResponse(access_token=token,expires_at=expires.isoformat())
@router.post("/logout",status_code=204)
def logout(credentials:HTTPAuthorizationCredentials=Depends(bearer),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    payload=decode_token(credentials.credentials); expires=datetime.fromtimestamp(payload["exp"],timezone.utc)
    db.add(RevokedToken(digest=token_digest(credentials.credentials),expires_at=expires)); db.commit()
