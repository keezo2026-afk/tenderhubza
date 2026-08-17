from fastapi import APIRouter,Depends,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.dependencies import require_admin
from app.core.database import get_db
from app.models import ConnectorRun,Source,User
from app.schemas.domain import ConnectorRunOut
router=APIRouter(prefix="/admin",tags=["admin"])
@router.get("/health")
def admin_health(admin:User=Depends(require_admin)):return {"status":"ok","admin":True,"components":{"connectors":"configured","workers":"command_driven"}}
@router.get("/connector-runs",response_model=list[ConnectorRunOut])
def connector_runs(source_id:str|None=None,limit:int=Query(50,ge=1,le=200),db:Session=Depends(get_db),admin:User=Depends(require_admin)):
 query=select(ConnectorRun).order_by(ConnectorRun.started_at.desc()).limit(limit)
 if source_id:query=query.where(ConnectorRun.source_id==source_id)
 return list(db.scalars(query))
@router.get("/sources/monitoring")
def source_monitoring(db:Session=Depends(get_db),admin:User=Depends(require_admin)):
 sources=list(db.scalars(select(Source).order_by(Source.name)));result=[]
 for source in sources:
  run=db.scalar(select(ConnectorRun).where(ConnectorRun.source_id==source.id).order_by(ConnectorRun.started_at.desc()).limit(1));result.append({"id":source.id,"name":source.name,"active":source.active,"last_success":source.last_successful_run,"last_failure":source.last_failed_run,"last_run":run.started_at if run else None,"status":run.status if run else None,"records_discovered":run.records_discovered if run else 0,"records_inserted":run.records_inserted if run else 0,"records_updated":run.records_updated if run else 0,"records_failed":run.records_failed if run else 0})
 return result
