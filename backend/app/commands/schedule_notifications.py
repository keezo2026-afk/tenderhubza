import asyncio,signal
import structlog
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.notifications.delivery import NotificationDeliveryService
from app.notifications.service import NotificationService
from app.services.connector_execution import ConnectorAlreadyRunning,connector_lock
log=structlog.get_logger()
async def scheduler():
 settings=get_settings()
 if not settings.notification_schedule_enabled:log.info("notification_scheduler_disabled");return
 stop=asyncio.Event();loop=asyncio.get_running_loop()
 for sig in (signal.SIGINT,signal.SIGTERM):loop.add_signal_handler(sig,stop.set)
 while not stop.is_set():
  try:
   with SessionLocal() as db:
    with connector_lock(db,"notification-jobs"):
     created=NotificationService(db).create_closing_reminders();db.commit();delivered=await NotificationDeliveryService(db).deliver_pending();log.info("notification_batch_completed",created=created,**delivered)
  except ConnectorAlreadyRunning:log.info("notification_batch_skipped",reason="already_running")
  except Exception as exc:log.exception("notification_batch_failed",error_type=type(exc).__name__)
  try:await asyncio.wait_for(stop.wait(),settings.notification_schedule_interval_minutes*60)
  except asyncio.TimeoutError:pass
if __name__=="__main__":asyncio.run(scheduler())
