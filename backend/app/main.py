import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import ApiError, error_body
from app.core.logging import configure_logging
from app.schemas.common import ErrorResponse

settings = get_settings()
configure_logging(settings.log_level)
log = structlog.get_logger()
ERROR_RESPONSES = {
    code: {"model": ErrorResponse, "description": description}
    for code, description in [
        (400, "Bad request"),
        (401, "Authentication required"),
        (403, "Forbidden"),
        (404, "Not found"),
        (409, "Conflict"),
        (422, "Validation error"),
        (429, "Rate limited"),
        (500, "Server error"),
    ]
}
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    responses=ERROR_RESPONSES,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    response = await call_next(request)
    log.info("request", method=request.method, path=request.url.path, status=response.status_code)
    return response


@app.exception_handler(ApiError)
async def api_error(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message, exc.details),
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    details = {
        "fields": [
            {"path": ".".join(str(x) for x in e["loc"]), "message": e["msg"], "type": e["type"]}
            for e in exc.errors()
        ]
    }
    return JSONResponse(
        status_code=422, content=error_body("VALIDATION_ERROR", "Invalid request", details)
    )


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    code = {
        401: "UNAUTHENTICATED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        429: "RATE_LIMITED",
    }.get(exc.status_code, "HTTP_ERROR")
    message = (
        exc.detail if isinstance(exc.detail, str) else exc.detail.get("message", "Request failed")
    )
    return JSONResponse(
        status_code=exc.status_code, content=error_body(code, message), headers=exc.headers
    )


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("unhandled_error", path=request.url.path)
    return JSONResponse(
        status_code=500, content=error_body("INTERNAL_ERROR", "An unexpected error occurred")
    )


app.include_router(api_router)
