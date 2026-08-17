from math import ceil
from fastapi import APIRouter,Depends,Query,Response
from sqlalchemy import func,select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import SavedTender,Tender,User
from app.schemas.common import Page
from app.schemas.domain import SavedTenderItem,TenderCard,TenderIdsRequest,TenderSavedState
router=APIRouter(tags=["saved tenders"])
@router.post("/tenders/{tender_id}/save",response_model=TenderSavedState,status_code=201)
def save_tender(tender_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 if not db.get(Tender,tender_id):raise ApiError(404,"TENDER_NOT_FOUND","Tender not found")
 existing=db.scalar(select(SavedTender).where(SavedTender.user_id==user.id,SavedTender.tender_id==tender_id))
 if not existing:
  db.add(SavedTender(user_id=user.id,tender_id=tender_id))
  try:db.commit()
  except IntegrityError:db.rollback()
 return TenderSavedState(tender_id=tender_id,saved=True)
@router.delete("/tenders/{tender_id}/save",status_code=204)
def unsave_tender(tender_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 item=db.scalar(select(SavedTender).where(SavedTender.user_id==user.id,SavedTender.tender_id==tender_id))
 if item:db.delete(item);db.commit()
 return Response(status_code=204)
@router.get("/tenders/{tender_id}/saved",response_model=TenderSavedState)
def saved_state(tender_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 if not db.get(Tender,tender_id):raise ApiError(404,"TENDER_NOT_FOUND","Tender not found")
 saved=db.scalar(select(SavedTender.id).where(SavedTender.user_id==user.id,SavedTender.tender_id==tender_id)) is not None;return TenderSavedState(tender_id=tender_id,saved=saved)
@router.post("/users/me/saved-tender-status",response_model=list[TenderSavedState])
def saved_states(data:TenderIdsRequest,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 ids=set(db.scalars(select(SavedTender.tender_id).where(SavedTender.user_id==user.id,SavedTender.tender_id.in_(data.tender_ids))).all());return [TenderSavedState(tender_id=x,saved=x in ids) for x in data.tender_ids]
@router.get("/users/me/saved-tenders",response_model=Page[SavedTenderItem])
def list_saved(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
 base=select(SavedTender,Tender).join(Tender,Tender.id==SavedTender.tender_id).where(SavedTender.user_id==user.id);total=db.scalar(select(func.count()).select_from(SavedTender).where(SavedTender.user_id==user.id)) or 0;rows=db.execute(base.order_by(SavedTender.created_at.desc()).offset((page-1)*page_size).limit(page_size)).all();items=[SavedTenderItem(saved_at=s.created_at,tender=TenderCard.model_validate(t)) for s,t in rows];return Page(items=items,page=page,page_size=page_size,total=total,total_pages=ceil(total/page_size) if total else 0)
