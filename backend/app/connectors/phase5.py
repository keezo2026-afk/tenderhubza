from app.connectors.municipal.ethekwini import EThekwiniConnector
from app.connectors.soe.eskom import EskomConnector
from app.sources.registry import connector_registry


def register_phase5_connectors():
    for slug, implementation in [
        ("ethekwini-municipality", EThekwiniConnector),
        ("eskom-tender-bulletin", EskomConnector),
    ]:
        if connector_registry.get(slug) is None:
            connector_registry.register(slug, implementation)
    return connector_registry
