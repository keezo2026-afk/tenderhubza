"""Stable, source-focused connector contract."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from app.ingestion.contracts import (
    DiscoveredItem,
    DocumentReference,
    NormalizedTender,
    RawPayload,
)


@dataclass(frozen=True)
class ConnectorCapabilities:
    supports_incremental: bool = False
    supports_documents: bool = False
    supports_updates: bool = True
    supports_pagination: bool = False
    supports_date_filtering: bool = False
    supports_api: bool = False
    supports_html: bool = False
    supports_pdf: bool = False


@dataclass(frozen=True)
class ConnectorHealth:
    healthy: bool
    message: str


class TenderConnector(ABC):
    """Connectors contain source assumptions, never persistence policy."""

    NAME = "unconfigured-connector"
    VERSION = "0.0.0"
    capabilities = ConnectorCapabilities()

    @abstractmethod
    async def discover(self) -> Iterable[DiscoveredItem]: ...

    @abstractmethod
    async def fetch(self, item: DiscoveredItem) -> RawPayload: ...

    @abstractmethod
    async def parse(self, payload: RawPayload) -> dict[str, Any]: ...

    @abstractmethod
    async def normalize(self, parsed: dict[str, Any]) -> NormalizedTender: ...

    @abstractmethod
    async def download_documents(self, tender: NormalizedTender) -> Iterable[DocumentReference]: ...

    async def health_check(self) -> ConnectorHealth:
        return ConnectorHealth(True, "No connector-specific health check configured")
