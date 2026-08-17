from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ConnectorRun, Source

FAILURES = {
    "ConnectError": "TCP_FAILURE",
    "ConnectTimeout": "TIMEOUT",
    "ReadTimeout": "TIMEOUT",
    "PermanentSourceError": "SCHEMA_CHANGE",
    "JSONDecodeError": "PARSE_FAILURE",
}


def classify_failure(error: Exception | str | None) -> str:
    if not error:
        return "UNKNOWN"
    text = str(error)
    name = type(error).__name__ if isinstance(error, Exception) else text
    for code in [403, 404, 408, 429, 500, 502, 503]:
        if str(code) in text:
            return f"HTTP_{code}"
    if "SSL" in text or "TLS" in text:
        return "TLS_FAILURE"
    if "DNS" in text or "gaierror" in text:
        return "DNS_FAILURE"
    return FAILURES.get(name, "UNKNOWN")


def health_for(source: Source, now=None):
    now = now or datetime.now(UTC)
    if source.status in {"BLOCKED", "RETIRED"}:
        return source.status
    if source.consecutive_failures >= 3:
        return "FAILING"
    success = source.last_successful_run
    if success:
        success = success if success.tzinfo else success.replace(tzinfo=UTC)
        if now - success > timedelta(minutes=max(source.polling_interval_minutes, 1) * 2):
            return "STALE"
    if source.consecutive_failures:
        return "WARNING"
    return "HEALTHY" if source.last_successful_run else "WARNING"


def apply_run_health(db: Session, source: Source, run: ConnectorRun):
    source.last_attempted_at = run.completed_at
    if run.status in {"SUCCESS", "SUCCESS_WITH_ZERO_RESULTS"}:
        source.consecutive_failures = 0
        source.last_error_category = None
        if run.records_discovered:
            source.last_tender_discovered_at = run.completed_at
        prior = db.scalar(
            select(ConnectorRun)
            .where(
                ConnectorRun.source_id == source.id,
                ConnectorRun.id != run.id,
                ConnectorRun.records_discovered > 0,
            )
            .order_by(ConnectorRun.started_at.desc())
            .limit(1)
        )
        run.zero_result_anomaly = run.records_discovered == 0 and prior is not None
        if run.zero_result_anomaly and source.status == "ACTIVE":
            source.status = "FAILING"
    elif run.status == "FAILED":
        source.consecutive_failures += 1
        source.last_error_category = run.error_category or "UNKNOWN"
        if source.consecutive_failures >= 3 and source.status == "ACTIVE":
            source.status = "FAILING"
