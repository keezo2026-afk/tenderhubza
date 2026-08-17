from pathlib import Path

from app.connectors.national.etenders import ETendersConnector
from app.core.database import Base
from app.models import Notification, Tender, User
from app.models.auth import RefreshToken
from app.models.geography import GeographyResolutionIssue
from app.models.ingestion import ConnectorRun
from app.models.notifications import NotificationDeviceDelivery
from app.models.saved import SavedSearch
from app.models.sources import Source
from app.models.tenders import TenderDuplicateCandidate
from app.models.users import Profile


def test_models_are_organized_without_changing_table_identity():
    from app.models.entities import User as CompatibilityUser

    assert CompatibilityUser is User
    assert User.__tablename__ == "users"
    assert Tender.__tablename__ == "tenders"
    assert Notification.__tablename__ == "notifications"
    assert {
        RefreshToken.__tablename__,
        GeographyResolutionIssue.__tablename__,
        ConnectorRun.__tablename__,
        NotificationDeviceDelivery.__tablename__,
        SavedSearch.__tablename__,
        Source.__tablename__,
        TenderDuplicateCandidate.__tablename__,
        Profile.__tablename__,
    } <= set(Base.metadata.tables)


def test_connector_declares_future_safe_capabilities():
    capabilities = ETendersConnector.capabilities
    assert capabilities.supports_api
    assert capabilities.supports_incremental
    assert capabilities.supports_pagination
    assert capabilities.supports_date_filtering
    assert capabilities.supports_documents


def test_phase35_migration_uses_explicit_alembic_operations():
    migration = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "0007_phase35_architecture_hardening.py"
    ).read_text()
    assert "metadata.create_all" not in migration
    assert "op.create_table" in migration
    assert "op.add_column" in migration
    assert "op.create_index" in migration
