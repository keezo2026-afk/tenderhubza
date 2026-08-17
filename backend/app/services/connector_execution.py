import fcntl
from contextlib import contextmanager
from datetime import date, timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.connectors.national.etenders import ETendersConnector
from app.core.config import get_settings
from app.ingestion.etenders_runner import ETendersIngestionService
from app.models import ConnectorState, Source


class ConnectorAlreadyRunning(RuntimeError):
    pass


@contextmanager
def connector_lock(db: Session, key: str):
    if db.bind.dialect.name == "postgresql":
        acquired = bool(
            db.scalar(text("SELECT pg_try_advisory_lock(hashtext(:key))").bindparams(key=key))
        )
        if not acquired:
            raise ConnectorAlreadyRunning(f"connector {key} is already running")
        try:
            yield
        finally:
            db.execute(text("SELECT pg_advisory_unlock(hashtext(:key))").bindparams(key=key))
            db.commit()
    else:
        path = f"/tmp/tenderhub-{key}.lock"
        handle = open(path, "w")
        try:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ConnectorAlreadyRunning(f"connector {key} is already running")
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
            handle.close()


async def execute_etenders(
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int | None = None,
):
    settings = get_settings()
    source = db.scalar(select(Source).where(Source.connector_type == "ETENDERS_OCDS"))
    if not source:
        raise RuntimeError("National Treasury source is not registered; run migrations")
    state = db.get(ConnectorState, source.id)
    end = date_to or date.today()
    start = date_from or (
        (state.high_water_date - timedelta(days=settings.etenders_overlap_days))
        if state and state.high_water_date
        else end - timedelta(days=settings.etenders_initial_sync_days)
    )
    if start > end:
        raise ValueError("date_from cannot be after date_to")
    connector = ETendersConnector(
        page,
        page_size or settings.etenders_page_size,
        start,
        end,
        settings.connector_timeout_seconds,
        settings.connector_max_attempts,
    )
    with connector_lock(db, connector.NAME):
        return await ETendersIngestionService(db, connector).run(source, high_water_candidate=end)
