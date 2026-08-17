import asyncio,signal
import structlog
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.connector_execution import ConnectorAlreadyRunning,execute_etenders
log=structlog.get_logger()
async def scheduler():
 settings=get_settings()
 if not settings.connector_schedule_enabled:log.info("connector_scheduler_disabled");return
 stop=asyncio.Event();loop=asyncio.get_running_loop()
 for sig in (signal.SIGINT,signal.SIGTERM):loop.add_signal_handler(sig,stop.set)
 log.info("connector_scheduler_started",interval_minutes=settings.connector_schedule_interval_minutes)
 while not stop.is_set():
  try:
   with SessionLocal() as db:
    run=await execute_etenders(db);log.info("scheduled_connector_completed",run_id=run.id,status=run.status,discovered=run.records_discovered,inserted=run.records_inserted,updated=run.records_updated,skipped=run.records_skipped,failed=run.records_failed)
  except ConnectorAlreadyRunning:log.info("scheduled_connector_skipped",reason="already_running")
  except Exception as exc:log.exception("scheduled_connector_failed",error_type=type(exc).__name__)
  try:await asyncio.wait_for(stop.wait(),timeout=settings.connector_schedule_interval_minutes*60)
  except asyncio.TimeoutError:pass
 log.info("connector_scheduler_stopped")
if __name__=="__main__":asyncio.run(scheduler())
