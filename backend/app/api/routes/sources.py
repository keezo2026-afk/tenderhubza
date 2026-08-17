from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.api.dependencies import require_admin
from app.core.database import get_db
from app.models import Source,SourceType,User
from app.schemas.common import Page
from app.schemas.domain import SourceCreate,SourceOut
router=APIRouter(prefix="/sources",tags=["sources"])
@router.get("",response_model=Page[SourceOut])
def sources(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),db:Session=Depends(get_db)):
    total=db.scalar(select(func.count()).select_from(Source)) or 0; return Page(items=list(db.scalars(select(Source).offset((page-1)*page_size).limit(page_size)).all()),page=page,page_size=page_size,total=total,total_pages=(total+page_size-1)//page_size if total else 0)
@router.post("",response_model=SourceOut,status_code=201)
def create_source(data:SourceCreate,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    if data.source_type not in {v.value for v in SourceType}: raise HTTPException(422,detail={"code":"INVALID_SOURCE_TYPE","message":"Unsupported source type"})
    item=Source(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item
