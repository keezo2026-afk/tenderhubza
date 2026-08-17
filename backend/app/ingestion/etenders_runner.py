from dataclasses import asdict,replace
from datetime import datetime,timezone
from decimal import Decimal
import time
from sqlalchemy import select
from sqlalchemy.orm import Session
import structlog
from app.connectors.national.etenders import ETendersConnector
from app.ingestion.contracts import NormalizedTender
from app.models import ConnectorRun,Province,RawIngestion,Source,Tender,TenderDocument,TenderDuplicateCandidate,TenderSourceVersion
log=structlog.get_logger()
class ETendersIngestionService:
 def __init__(self,db:Session,connector:ETendersConnector):self.db=db;self.connector=connector
 async def run(self,source:Source)->ConnectorRun:
  run=ConnectorRun(source_id=source.id,connector_name=self.connector.NAME,connector_version=self.connector.VERSION);self.db.add(run);self.db.commit();started=time.monotonic()
  try:
   items=list(await self.connector.discover());run.records_discovered=len(items);self.db.commit()
  except Exception as exc:return self._finish(run,"FAILED",exc,started,source)
  for item in items:
   raw=None
   try:
    payload=await self.connector.fetch(item);run.records_fetched+=1
    raw=RawIngestion(source_id=source.id,source_identifier=payload.source_identifier,original_source_url=payload.source_url,request_url=payload.request_url,http_status=payload.http_status,response_timestamp=payload.ingested_at,content_type=payload.content_type,raw_payload=payload.payload,ingested_at=payload.ingested_at,connector_version=payload.connector_version,payload_hash=payload.checksum,source_release_id=payload.source_release_id,ocds_identifier=payload.source_identifier,document_references=[],normalization_status="PENDING",processing_status="RAW_PERSISTED")
    self.db.add(raw);self.db.commit();self.db.refresh(raw) # mandatory raw-first durability boundary
    parsed=await self.connector.parse(payload);run.records_parsed+=1
    normalized=replace(await self.connector.normalize(parsed),payload_hash=payload.checksum);run.records_normalized+=1
    errors=self._validate(normalized)
    if errors:raise ValueError("; ".join(errors))
    action=self._persist(source,raw,normalized)
    if action=="inserted":run.records_inserted+=1
    elif action=="updated":run.records_updated+=1
    else:run.records_skipped+=1
    raw.normalization_status="SUCCESS";raw.processing_status="PERSISTED";raw.document_references=[asdict(d) for d in normalized.documents];self.db.commit()
   except Exception as exc:
    self.db.rollback();run=self.db.get(ConnectorRun,run.id)
    if raw:
     raw=self.db.get(RawIngestion,raw.id);raw.normalization_status="FAILED";raw.processing_status="FAILED";raw.error=str(exc)[:2000]
    run.records_failed+=1;run.error_count+=1;run.last_error=str(exc)[:2000];self.db.commit();log.warning("ingestion_item_failed",source_identifier=item.source_identifier,error=type(exc).__name__)
  status="SUCCESS" if run.records_failed==0 else ("PARTIAL" if run.records_inserted+run.records_updated+run.records_skipped else "FAILED")
  return self._finish(run,status,None,started,source)
 def _validate(self,t:NormalizedTender)->list[str]:
  errors=[]
  if not t.source_reference or len(t.source_reference)>255:errors.append("valid source reference is required")
  if not t.title or len(t.title)>500:errors.append("valid title is required")
  if not t.organisation or len(t.organisation)>255:errors.append("valid organisation is required")
  if t.reference_number and len(t.reference_number)>255:errors.append("reference number is too long")
  if t.contact_email and len(t.contact_email)>320:errors.append("contact email is too long")
  if not t.source_url.startswith("https://") or len(t.source_url)>2048:errors.append("valid HTTPS source URL is required")
  if t.estimated_value is not None and t.estimated_value<0:errors.append("estimated value cannot be negative")
  return errors
 def _persist(self,source:Source,raw:RawIngestion,t:NormalizedTender)->str:
  tender=self.db.scalar(select(Tender).where(Tender.source_id==source.id,Tender.source_reference==t.source_reference))
  values={k:v for k,v in asdict(t).items() if k not in {"documents"}};province=self.db.scalar(select(Province).where(Province.name==t.province)) if t.province else None;values["province_id"]=province.id if province else None
  if tender and tender.payload_hash==t.payload_hash:return "skipped"
  if tender:
   changes={k:{"from":str(getattr(tender,k)),"to":str(v)} for k,v in values.items() if hasattr(tender,k) and getattr(tender,k)!=v}
   for k,v in values.items():
    if hasattr(tender,k):setattr(tender,k,v)
   self.db.query(TenderDocument).filter(TenderDocument.tender_id==tender.id).delete();action="updated"
  else:
   tender=Tender(source_id=source.id,**values);self.db.add(tender);self.db.flush();changes={"created":True};action="inserted"
  for doc in t.documents:self.db.add(TenderDocument(tender_id=tender.id,name=doc.name,source_url=doc.url,mime_type=doc.media_type))
  self.db.add(TenderSourceVersion(tender_id=tender.id,raw_ingestion_id=raw.id,change_summary=changes))
  if action=="inserted" and tender.reference_number:
   candidate=self.db.scalar(select(Tender).where(Tender.source_id!=source.id,Tender.reference_number==tender.reference_number,Tender.organisation==tender.organisation).limit(1))
   if candidate:self.db.add(TenderDuplicateCandidate(tender_id=tender.id,candidate_tender_id=candidate.id,reason="same reference number and organisation across sources"))
  self.db.flush();return action
 def _finish(self,run,status,error,started,source):
  run=self.db.get(ConnectorRun,run.id);run.status=status;run.completed_at=datetime.now(timezone.utc);run.duration_seconds=Decimal(str(round(time.monotonic()-started,3)))
  if error:run.error_count+=1;run.last_error=str(error)[:2000]
  if status=="SUCCESS":source.last_successful_run=run.completed_at;source.last_error=None
  elif status in ("FAILED","PARTIAL"):source.last_failed_run=run.completed_at;source.last_error=run.last_error
  self.db.commit();self.db.refresh(run);return run
