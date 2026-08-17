import threading,time
from collections import defaultdict,deque
from fastapi import Request
from app.core.config import get_settings
from app.core.errors import ApiError
class InMemoryRateLimiter:
    """Single-process limiter. Replace with shared storage when horizontally scaling."""
    def __init__(self): self._events=defaultdict(deque);self._lock=threading.Lock()
    def check(self,key:str,limit:int,window_seconds:int=60):
        now=time.monotonic()
        with self._lock:
            events=self._events[key]
            while events and events[0]<=now-window_seconds: events.popleft()
            if len(events)>=limit: raise ApiError(429,"RATE_LIMITED","Too many requests. Please try again later.",headers={"Retry-After":str(window_seconds)})
            events.append(now)
limiter=InMemoryRateLimiter()
def limit(request:Request,bucket:str,maximum:int): limiter.check(f"{bucket}:{request.client.host if request.client else 'unknown'}",maximum)
