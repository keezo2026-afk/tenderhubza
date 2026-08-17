from datetime import datetime,timedelta,timezone
from fastapi import APIRouter,Depends,Query
from sqlalchemy import case,func,select
from sqlalchemy.orm import Session
from app.api.dependencies import require_admin
from app.core.database import get_db
from app.models import ConnectorRun,Notification,NotificationDelivery,Source,Tender,TenderDocument,TenderDuplicateCandidate,User
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
@router.get("/data-quality")
def data_quality(db:Session=Depends(get_db),admin:User=Depends(require_admin)):
 now=datetime.now(timezone.utc);today=now.replace(hour=0,minute=0,second=0,microsecond=0);week=now-timedelta(days=7);month=now-timedelta(days=30)
 source_total=db.scalar(select(func.count()).select_from(Source)) or 0;source_active=db.scalar(select(func.count()).select_from(Source).where(Source.active.is_(True))) or 0;source_failed=db.scalar(select(func.count()).select_from(Source).where(Source.last_failed_run.is_not(None),func.coalesce(Source.last_successful_run,today-timedelta(days=36500))<Source.last_failed_run)) or 0
 def tenders_since(value):return db.scalar(select(func.count()).select_from(Tender).where(Tender.ingested_at>=value)) or 0
 sums=db.execute(select(func.coalesce(func.sum(ConnectorRun.records_inserted),0),func.coalesce(func.sum(ConnectorRun.records_updated),0),func.coalesce(func.sum(ConnectorRun.records_skipped),0),func.coalesce(func.sum(ConnectorRun.records_failed),0)).where(ConnectorRun.started_at>=month)).one()
 notification_counts={kind:(db.scalar(select(func.count()).select_from(Notification).where(Notification.created_at>=today,Notification.type==kind)) or 0) for kind in ["NEW_TENDER_MATCH","TENDER_CLOSING_SOON","TENDER_UPDATED"]};delivery_counts={f"{channel.lower()}_{status.lower()}":(db.scalar(select(func.count()).select_from(NotificationDelivery).where(NotificationDelivery.attempted_at>=today,NotificationDelivery.channel==channel,NotificationDelivery.status==status)) or 0) for channel in ["PUSH","EMAIL"] for status in ["SENT","FAILED"]}
 return {"generated_at":now,"notifications":{"today":sum(notification_counts.values()),"by_type":notification_counts,"deliveries":delivery_counts},"sources":{"total":source_total,"active":source_active,"failed":source_failed,"last_successful_run":db.scalar(select(func.max(Source.last_successful_run)))},"tender_ingestion":{"today":tenders_since(today),"last_7_days":tenders_since(week),"last_30_days":tenders_since(month)},"processing_last_30_days":{"inserted":sums[0],"updated":sums[1],"skipped":sums[2],"failed":sums[3]},"duplicates":{"candidates":db.scalar(select(func.count()).select_from(TenderDuplicateCandidate)) or 0},"documents":{"discovered":db.scalar(select(func.count()).select_from(TenderDocument)) or 0}}
