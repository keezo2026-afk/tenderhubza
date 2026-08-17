"""Multi-connector orchestration with connector and run isolation."""

from dataclasses import dataclass

import structlog
from sqlalchemy.orm import Session

from app.connectors.base import TenderConnector
from app.ingestion.engine import IngestionEngine
from app.models import Source

log = structlog.get_logger()


@dataclass(frozen=True)
class ConnectorExecution:
    source_id: str
    connector: str
    run_id: str | None
    status: str
    error_type: str | None = None


class IngestionCoordinator:
    """Runs connectors independently so one source cannot stop another."""

    def __init__(self, db: Session):
        self.db = db

    async def run_connectors(
        self, jobs: list[tuple[Source, TenderConnector]]
    ) -> list[ConnectorExecution]:
        executions: list[ConnectorExecution] = []
        for source, connector in jobs:
            try:
                run = await IngestionEngine(self.db, connector).run(source)
                executions.append(ConnectorExecution(source.id, connector.NAME, run.id, run.status))
            except Exception as exc:
                self.db.rollback()
                log.warning(
                    "connector_isolated_failure",
                    source_id=source.id,
                    connector=connector.NAME,
                    connector_version=connector.VERSION,
                    error_type=type(exc).__name__,
                )
                executions.append(
                    ConnectorExecution(
                        source.id,
                        connector.NAME,
                        None,
                        "FAILED",
                        type(exc).__name__,
                    )
                )
        return executions


# Compatibility alias for callers that imported the old conceptual pipeline.
IngestionPipeline = IngestionCoordinator
