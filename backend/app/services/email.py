import asyncio,smtplib
from email.message import EmailMessage
from typing import Protocol
from app.core.config import Settings
class EmailProvider(Protocol):
 async def send_password_reset(self,email:str,reset_url:str)->None:...
 async def send_notification(self,email:str,subject:str,body:str)->str|None:...
class DevelopmentEmailProvider:
 """No external delivery. The API returns a token only in development."""
 async def send_password_reset(self,email:str,reset_url:str)->None:return None
 async def send_notification(self,email:str,subject:str,body:str)->str|None:return None
class SmtpEmailProvider:
 def __init__(self,settings:Settings):
  if not settings.smtp_host or not settings.smtp_from_email:raise RuntimeError("SMTP_HOST and SMTP_FROM_EMAIL are required")
  self.settings=settings
 async def send_password_reset(self,email:str,reset_url:str)->None:await asyncio.to_thread(self._send,email,"Reset your TenderHub SA password",f"Use this one-time link to reset your password:\n\n{reset_url}\n\nIf you did not request this, ignore this message.")
 async def send_notification(self,email:str,subject:str,body:str)->str|None:await asyncio.to_thread(self._send,email,subject,body);return None
 def _send(self,email:str,subject:str,body:str):
  message=EmailMessage();message["Subject"]=subject;message["From"]=self.settings.smtp_from_email;message["To"]=email;message.set_content(body)
  with smtplib.SMTP(self.settings.smtp_host,self.settings.smtp_port,timeout=20) as smtp:
   if self.settings.smtp_starttls:smtp.starttls()
   if self.settings.smtp_username:smtp.login(self.settings.smtp_username,self.settings.smtp_password or "")
   smtp.send_message(message)
def email_provider(settings:Settings)->EmailProvider:
 if settings.mail_adapter=="development":return DevelopmentEmailProvider()
 if settings.mail_adapter=="smtp":return SmtpEmailProvider(settings)
 raise RuntimeError(f"Unsupported MAIL_ADAPTER: {settings.mail_adapter}")
