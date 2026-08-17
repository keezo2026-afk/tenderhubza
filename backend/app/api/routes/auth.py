from datetime import datetime,timedelta,timezone
from uuid import uuid4
from fastapi import APIRouter,Depends,Request
from sqlalchemy import select,update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.dependencies import bearer,get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import ApiError
from app.core.rate_limit import limit
from app.core.security import create_access_token,create_opaque_token,hash_password,token_digest,verify_password
from app.models import PasswordResetToken,Profile,RefreshToken,RevokedToken,User
from app.schemas.auth import *
from app.schemas.domain import UserOut
router=APIRouter(prefix="/auth",tags=["auth"])
def _tokens(db,user,family_id=None)->TokenResponse:
 settings=get_settings();access,access_exp=create_access_token(user.id,user.role);refresh=create_opaque_token();refresh_exp=datetime.now(timezone.utc)+timedelta(days=settings.refresh_token_expire_days);db.add(RefreshToken(digest=token_digest(refresh),user_id=user.id,family_id=family_id or str(uuid4()),expires_at=refresh_exp));db.commit();return TokenResponse(access_token=access,refresh_token=refresh,access_expires_at=access_exp.isoformat(),refresh_expires_at=refresh_exp.isoformat())
@router.post("/register",response_model=UserOut,status_code=201)
def register(data:RegisterRequest,request:Request,db:Session=Depends(get_db)):
 limit(request,"register",get_settings().auth_rate_limit_per_minute);email=data.email.lower()
 if db.scalar(select(User).where(User.email==email)):raise ApiError(409,"EMAIL_EXISTS","An account with this email already exists")
 user=User(email=email,password_hash=hash_password(data.password),first_name=data.first_name,last_name=data.last_name,phone=data.phone);user.profile=Profile(display_name=f"{data.first_name} {data.last_name}",notification_preferences={});db.add(user)
 try:db.commit()
 except IntegrityError:db.rollback();raise ApiError(409,"EMAIL_EXISTS","An account with this email already exists")
 db.refresh(user);return user
@router.post("/login",response_model=TokenResponse)
def login(data:LoginRequest,request:Request,db:Session=Depends(get_db)):
 limit(request,"login",get_settings().auth_rate_limit_per_minute);user=db.scalar(select(User).where(User.email==data.email.lower()))
 if not user or not verify_password(data.password,user.password_hash):raise ApiError(401,"INVALID_CREDENTIALS","Email or password is incorrect")
 if user.status!="ACTIVE":raise ApiError(403,"ACCOUNT_DISABLED","Account is not active")
 return _tokens(db,user)
@router.post("/refresh",response_model=TokenResponse)
def refresh(data:RefreshRequest,request:Request,db:Session=Depends(get_db)):
 limit(request,"refresh",get_settings().auth_rate_limit_per_minute);digest=token_digest(data.refresh_token);record=db.get(RefreshToken,digest);now=datetime.now(timezone.utc)
 if not record:raise ApiError(401,"INVALID_REFRESH_TOKEN","Refresh token is invalid")
 expires=record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=timezone.utc)
 if record.used_at or record.revoked_at:
  db.execute(update(RefreshToken).where(RefreshToken.family_id==record.family_id).values(revoked_at=now));db.commit();raise ApiError(401,"REFRESH_TOKEN_REUSE","Refresh token reuse detected; session revoked")
 if expires<=now:raise ApiError(401,"EXPIRED_REFRESH_TOKEN","Refresh token has expired")
 user=db.get(User,record.user_id)
 if not user or user.status!="ACTIVE":raise ApiError(401,"INVALID_USER","User is unavailable")
 record.used_at=now;result=_tokens(db,user,record.family_id);record.replaced_by_digest=token_digest(result.refresh_token);db.commit();return result
@router.post("/logout",status_code=204)
def logout(data:LogoutRequest|None=None,credentials=Depends(bearer),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 from app.core.security import decode_token
 payload=decode_token(credentials.credentials);expires=datetime.fromtimestamp(payload["exp"],timezone.utc);db.add(RevokedToken(digest=token_digest(credentials.credentials),expires_at=expires))
 if data and data.refresh_token:
  record=db.get(RefreshToken,token_digest(data.refresh_token))
  if record:db.execute(update(RefreshToken).where(RefreshToken.family_id==record.family_id).values(revoked_at=datetime.now(timezone.utc)))
 db.commit()
@router.post("/password-reset/request",response_model=PasswordResetRequested)
def request_reset(data:PasswordResetRequest,request:Request,db:Session=Depends(get_db)):
 settings=get_settings();limit(request,"password-reset",settings.auth_rate_limit_per_minute);user=db.scalar(select(User).where(User.email==data.email.lower()));token=None
 if user:
  token=create_opaque_token();db.add(PasswordResetToken(digest=token_digest(token),user_id=user.id,expires_at=datetime.now(timezone.utc)+timedelta(minutes=settings.password_reset_expire_minutes)));db.commit()
 return PasswordResetRequested(development_token=token if settings.environment=="development" and settings.mail_adapter=="development" else None)
@router.post("/password-reset/confirm",status_code=204)
def confirm_reset(data:PasswordResetConfirm,request:Request,db:Session=Depends(get_db)):
 limit(request,"password-reset-confirm",get_settings().auth_rate_limit_per_minute);record=db.get(PasswordResetToken,token_digest(data.token));now=datetime.now(timezone.utc)
 if not record:raise ApiError(400,"INVALID_RESET_TOKEN","Password reset token is invalid or expired")
 expires=record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=timezone.utc)
 if record.used_at or expires<=now:raise ApiError(400,"INVALID_RESET_TOKEN","Password reset token is invalid or expired")
 user=db.get(User,record.user_id);user.password_hash=hash_password(data.new_password);record.used_at=now;db.execute(update(RefreshToken).where(RefreshToken.user_id==user.id).values(revoked_at=now));db.commit()
