from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
settings=get_settings(); configure_logging(settings.log_level); log=structlog.get_logger()
app=FastAPI(title=settings.app_name,version="0.1.0",docs_url="/api/docs",openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",")],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.middleware("http")
async def request_logging(request:Request,call_next):
    response=await call_next(request); log.info("request",method=request.method,path=request.url.path,status=response.status_code); return response
@app.exception_handler(Exception)
async def unhandled(request:Request,exc:Exception):
    log.exception("unhandled_error",path=request.url.path); return JSONResponse(status_code=500,content={"error":{"code":"INTERNAL_ERROR","message":"An unexpected error occurred"}})
app.include_router(api_router)
