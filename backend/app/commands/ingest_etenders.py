import argparse,asyncio
from datetime import date
from app.core.database import SessionLocal
from app.services.connector_execution import execute_etenders
async def main():
 parser=argparse.ArgumentParser();parser.add_argument("--date-from",type=date.fromisoformat);parser.add_argument("--date-to",type=date.fromisoformat);parser.add_argument("--page",type=int,default=1);parser.add_argument("--page-size",type=int);args=parser.parse_args()
 with SessionLocal() as db:
  run=await execute_etenders(db,args.date_from,args.date_to,args.page,args.page_size);print(f"run={run.id} status={run.status} discovered={run.records_discovered} fetched={run.records_fetched} parsed={run.records_parsed} normalized={run.records_normalized} inserted={run.records_inserted} updated={run.records_updated} skipped={run.records_skipped} failed={run.records_failed} duration={run.duration_seconds}s")
if __name__=="__main__":asyncio.run(main())
