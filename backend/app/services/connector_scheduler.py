from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.phase5 import register_phase5_connectors
from app.core.config import get_settings
from app.ingestion.engine import IngestionEngine
from app.models import ConnectorRegistration, Source
from app.services.connector_execution import ConnectorAlreadyRunning, connector_lock


@dataclass(frozen=True)
class ScheduledExecution:
    source_id: str
    connector_slug: str
    status: str
    run_id: str | None = None
    reason: str | None = None


def is_due(source, now):
    if not source.last_attempted_at:
        return True
    attempted = (
        source.last_attempted_at
        if source.last_attempted_at.tzinfo
        else source.last_attempted_at.replace(tzinfo=UTC)
    )
    return now - attempted >= timedelta(minutes=source.polling_interval_minutes)


async def run_due_connectors(db: Session, now=None):
    now = now or datetime.now(UTC)
    registry = register_phase5_connectors()
    settings = get_settings()
    rows = db.execute(
        select(Source, ConnectorRegistration)
        .join(ConnectorRegistration, ConnectorRegistration.source_id == Source.id)
        .where(
            Source.active.is_(True),
            Source.status == "ACTIVE",
            ConnectorRegistration.status == "ACTIVE",
        )
        .order_by(Source.priority, Source.name)
    ).all()
    results = []
    for source, registration in rows:
        if not is_due(source, now):
            results.append(
                ScheduledExecution(source.id, registration.slug, "SKIPPED", reason="NOT_DUE")
            )
            continue
        implementation = registry.get(registration.slug)
        if not implementation:
            source.last_attempted_at = now
            source.consecutive_failures += 1
            source.last_error_category = "UNKNOWN"
            db.commit()
            results.append(
                ScheduledExecution(
                    source.id, registration.slug, "REJECTED", reason="UNAPPROVED_CONNECTOR"
                )
            )
            continue
        try:
            import inspect

            kwargs = (
                {"max_redirects": settings.connector_max_redirects}
                if "max_redirects" in inspect.signature(implementation).parameters
                else {}
            )
            connector = implementation(**kwargs)
            with connector_lock(db, f"{source.id}:{registration.slug}"):
                high_water = (
                    now.date() if registration.slug == "national-treasury-etenders-ocds" else None
                )
                run = await IngestionEngine(db, connector).run(
                    source, high_water_candidate=high_water
                )
            results.append(ScheduledExecution(source.id, registration.slug, run.status, run.id))
        except ConnectorAlreadyRunning:
            results.append(
                ScheduledExecution(
                    source.id, registration.slug, "SKIPPED", reason="ALREADY_RUNNING"
                )
            )
        except Exception as exc:
            db.rollback()
            source.last_attempted_at = now
            source.consecutive_failures += 1
            source.last_error_category = "UNKNOWN"
            db.commit()
            results.append(
                ScheduledExecution(
                    source.id, registration.slug, "FAILED", reason=type(exc).__name__
                )
            )
    return results
