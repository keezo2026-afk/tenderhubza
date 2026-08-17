from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.api.dependencies import require_admin
from app.core.database import get_db
from app.models import Tender,User
from app.schemas.common import Page
from app.schemas.domain import TenderCreate,TenderOut
router=APIRouter(prefix="/tenders",tags=["tenders"])
@router.get("",response_model=Page[TenderOut])
def list_tenders(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),province:str|None=None,municipality:str|None=None,category:str|None=None,db:Session=Depends(get_db)):
    query=select(Tender); count=select(func.count()).select_from(Tender)
    for value,column in [(province,Tender.province),(municipality,Tender.municipality),(category,Tender.category)]:
        if value: query=query.where(column==value); count=count.where(column==value)
    items=db.scalars(query.order_by(Tender.closing_date.asc()).offset((page-1)*page_size).limit(page_size)).all()
    return Page(items=list(items),page=page,page_size=page_size,total=db.scalar(count) or 0)
@router.get("/{tender_id}",response_model=TenderOut)
def get_tender(tender_id:str,db:Session=Depends(get_db)):
    item=db.get(Tender,tender_id)
    if not item: raise HTTPException(404,detail={"code":"NOT_FOUND","message":"Tender not found"})
    return item
@router.post("",response_model=TenderOut,status_code=201,include_in_schema=False)
def create_tender(data:TenderCreate,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    item=Tender(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item
