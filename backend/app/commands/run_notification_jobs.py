import asyncio,json
from app.core.database import SessionLocal
from app.notifications.delivery import NotificationDeliveryService
from app.notifications.service import NotificationService
from app.services.connector_execution import connector_lock
async def main():
 with SessionLocal() as db:
  with connector_lock(db,"notification-jobs"):
   created=NotificationService(db).create_closing_reminders();db.commit();delivery=await NotificationDeliveryService(db).deliver_pending();print(json.dumps({"closing_notifications_created":created,"delivery":delivery}))
if __name__=="__main__":asyncio.run(main())
