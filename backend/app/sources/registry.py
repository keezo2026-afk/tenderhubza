from dataclasses import asdict

from app.connectors.base import TenderConnector


class ConnectorRegistry:
    def __init__(self):
        self._connectors = {}

    def register(self, slug: str, connector_type: type[TenderConnector]):
        if slug in self._connectors:
            raise ValueError(f"connector already registered: {slug}")
        self._connectors[slug] = connector_type

    def get(self, slug: str):
        return self._connectors.get(slug)

    def describe(self, slug: str):
        connector = self.get(slug)
        if not connector:
            return None
        return {
            "slug": slug,
            "name": connector.NAME,
            "version": connector.VERSION,
            "capabilities": asdict(connector.capabilities),
            "implementation_reference": f"{connector.__module__}.{connector.__name__}",
        }


connector_registry = ConnectorRegistry()
