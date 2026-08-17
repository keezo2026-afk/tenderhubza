from typing import Protocol
from app.core.config import Settings
class PushProvider(Protocol):
 async def send(self,token:str,title:str,body:str,data:dict[str,str])->str:...
class DevelopmentPushProvider:
 async def send(self,token:str,title:str,body:str,data:dict[str,str])->str:raise RuntimeError("development push provider does not deliver")
class FirebasePushProvider:
 def __init__(self,settings:Settings):
  if not settings.firebase_credentials_file:raise RuntimeError("FIREBASE_CREDENTIALS_FILE is required")
  import firebase_admin
  from firebase_admin import credentials
  try:firebase_admin.get_app()
  except ValueError:firebase_admin.initialize_app(credentials.Certificate(settings.firebase_credentials_file))
 async def send(self,token:str,title:str,body:str,data:dict[str,str])->str:
  import asyncio
  from firebase_admin import messaging
  message=messaging.Message(notification=messaging.Notification(title=title,body=body),data=data,token=token)
  return await asyncio.to_thread(messaging.send,message)
def push_provider(settings:Settings)->PushProvider:
 if settings.push_provider=="development":return DevelopmentPushProvider()
 if settings.push_provider=="firebase":return FirebasePushProvider(settings)
 raise RuntimeError(f"Unsupported PUSH_PROVIDER: {settings.push_provider}")
