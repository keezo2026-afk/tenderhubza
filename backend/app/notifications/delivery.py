from datetime import datetime,timedelta,timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
import structlog
from app.core.config import get_settings
from app.models import DeviceToken,Notification,NotificationDelivery,User
from app.notifications.push import DevelopmentPushProvider,push_provider
from app.services.email import DevelopmentEmailProvider,email_provider
log=structlog.get_logger()
class NotificationDeliveryService:
 def __init__(self,db:Session):self.db=db;self.settings=get_settings()
 async def deliver_pending(self,limit:int=100):
  deliveries=list(self.db.scalars(select(NotificationDelivery).where(NotificationDelivery.status=="PENDING",NotificationDelivery.available_at<=datetime.now(timezone.utc)).order_by(NotificationDelivery.available_at).limit(limit)));result={"sent":0,"failed":0,"skipped":0}
  for delivery in deliveries:
   notification=self.db.get(Notification,delivery.notification_id);delivery.attempt_count+=1;delivery.attempted_at=datetime.now(timezone.utc)
   try:
    if delivery.channel=="PUSH":await self._push(delivery,notification)
    elif delivery.channel=="EMAIL":await self._email(delivery,notification)
    else:delivery.status="SKIPPED";delivery.error_code="UNSUPPORTED_CHANNEL"
   except Exception as exc:delivery.status="PENDING" if delivery.attempt_count<3 else "FAILED";delivery.available_at=datetime.now(timezone.utc)+timedelta(minutes=5*delivery.attempt_count);delivery.error_code=type(exc).__name__;delivery.error_message=str(exc)[:500];log.warning("notification_delivery_failed",channel=delivery.channel,error_type=type(exc).__name__)
   result["sent" if delivery.status=="SENT" else "skipped" if delivery.status=="SKIPPED" else "failed"]+=1;self.db.commit()
  return result
 async def _push(self,delivery,notification):
  provider=push_provider(self.settings)
  if isinstance(provider,DevelopmentPushProvider):delivery.status="SKIPPED";delivery.error_code="DEVELOPMENT_PROVIDER";log.info("push_skipped",reason="development_provider");return
  tokens=list(self.db.scalars(select(DeviceToken.token).where(DeviceToken.user_id==notification.user_id,DeviceToken.active.is_(True))))
  if not tokens:delivery.status="SKIPPED";delivery.error_code="NO_ACTIVE_DEVICE";return
  ids=[]
  for token in tokens:ids.append(await provider.send(token,notification.title,notification.body,{"notification_id":notification.id,"tender_id":notification.tender_id or "","type":notification.type}))
  delivery.status="SENT";delivery.provider_message_id=",".join(ids)[:255];log.info("push_succeeded",device_count=len(tokens))
 async def _email(self,delivery,notification):
  provider=email_provider(self.settings)
  if isinstance(provider,DevelopmentEmailProvider):delivery.status="SKIPPED";delivery.error_code="DEVELOPMENT_PROVIDER";log.info("email_skipped",reason="development_provider");return
  user=self.db.get(User,notification.user_id);delivery.provider_message_id=await provider.send_notification(user.email,notification.title,notification.body);delivery.status="SENT";log.info("email_succeeded")
