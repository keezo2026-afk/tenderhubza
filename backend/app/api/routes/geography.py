from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Municipality,Province
from app.schemas.domain import MunicipalityOut,ProvinceOut
router=APIRouter(tags=["geography"])
@router.get("/provinces",response_model=list[ProvinceOut])
def provinces(db:Session=Depends(get_db)): return list(db.scalars(select(Province).order_by(Province.name)).all())
@router.get("/municipalities",response_model=list[MunicipalityOut])
def municipalities(province_id:str|None=None,db:Session=Depends(get_db)):
    query=select(Municipality).where(Municipality.active.is_(True))
    if province_id: query=query.where(Municipality.province_id==province_id)
    return list(db.scalars(query.order_by(Municipality.name)).all())
