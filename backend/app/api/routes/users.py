from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models import Profile, User
from app.schemas.domain import ProfileOut, ProfileUpdate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


def profile_out(user):
    profile = user.profile
    return ProfileOut(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        display_name=profile.display_name if profile else None,
        province=profile.province if profile else None,
        city=profile.city if profile else None,
    )


@router.get("/me/profile", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_user)):
    return profile_out(user)


@router.put("/me/profile", response_model=ProfileOut)
def update_profile(
    data: ProfileUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    user.first_name = data.first_name
    user.last_name = data.last_name
    user.phone = data.phone
    profile = user.profile or Profile(user_id=user.id, notification_preferences={})
    profile.display_name = f"{data.first_name} {data.last_name}"
    profile.province = data.province
    profile.city = data.city
    if not user.profile:
        db.add(profile)
    db.commit()
    db.refresh(user)
    return profile_out(user)
