import argparse,asyncio
from datetime import date,timedelta
from sqlalchemy import select
from app.connectors.national.etenders import ETendersConnector
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.ingestion.etenders_runner import ETendersIngestionService
from app.models import Source
async def main():
 parser=argparse.ArgumentParser();parser.add_argument("--date-from",type=date.fromisoformat,default=date.today()-timedelta(days=7));parser.add_argument("--date-to",type=date.fromisoformat,default=date.today());parser.add_argument("--page",type=int,default=1);parser.add_argument("--page-size",type=int);args=parser.parse_args();settings=get_settings()
 with SessionLocal() as db:
  source=db.scalar(select(Source).where(Source.connector_type=="ETENDERS_OCDS"))
  if not source:raise SystemExit("National Treasury source is not registered; run migrations")
  connector=ETendersConnector(args.page,args.page_size or settings.etenders_page_size,args.date_from,args.date_to,settings.connector_timeout_seconds,settings.connector_max_attempts);run=await ETendersIngestionService(db,connector).run(source);print(f"run={run.id} status={run.status} discovered={run.records_discovered} inserted={run.records_inserted} updated={run.records_updated} skipped={run.records_skipped} failed={run.records_failed}")
if __name__=="__main__":asyncio.run(main())
