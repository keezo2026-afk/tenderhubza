import asyncio
import signal

import structlog

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.connector_scheduler import run_due_connectors

log = structlog.get_logger()


async def scheduler():
    settings = get_settings()
    if not settings.connector_schedule_enabled:
        log.info("connector_scheduler_disabled")
        return
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    log.info(
        "connector_scheduler_started", interval_minutes=settings.connector_schedule_interval_minutes
    )
    while not stop.is_set():
        try:
            with SessionLocal() as db:
                results = await run_due_connectors(db)
                log.info(
                    "scheduled_connector_cycle_completed",
                    results=[result.__dict__ for result in results],
                )
        except Exception as exc:
            log.exception("scheduled_connector_failed", error_type=type(exc).__name__)
        try:
            await asyncio.wait_for(
                stop.wait(), timeout=settings.connector_schedule_interval_minutes * 60
            )
        except TimeoutError:
            pass
    log.info("connector_scheduler_stopped")


if __name__ == "__main__":
    asyncio.run(scheduler())
