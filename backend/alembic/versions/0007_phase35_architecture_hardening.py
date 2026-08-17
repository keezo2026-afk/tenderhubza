"""Phase 3.5 architecture hardening.

This is the first migration written under the explicit-operation rule. Conditional guards are
required only because historical revisions call current ORM metadata during a fresh upgrade.

Revision ID: 0007
"""

from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def _has_column(table: str, name: str) -> bool:
    return name in {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def _has_index(table: str, name: str) -> bool:
    return name in {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table)}


def upgrade() -> None:
    if not _has_column("tender_duplicate_candidates", "confidence"):
        op.add_column("tender_duplicate_candidates", sa.Column("confidence", sa.Numeric(5, 4)))
    if not _has_column("tender_duplicate_candidates", "match_method"):
        op.add_column(
            "tender_duplicate_candidates",
            sa.Column(
                "match_method", sa.String(50), nullable=False, server_default="EXACT_REFERENCE"
            ),
        )
    if not _has_column("tender_duplicate_candidates", "signals"):
        op.add_column(
            "tender_duplicate_candidates",
            sa.Column("signals", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        )
    if not _has_table("geography_resolution_issues"):
        op.create_table(
            "geography_resolution_issues",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("source_id", sa.String(36), nullable=False),
            sa.Column("raw_ingestion_id", sa.String(36)),
            sa.Column("tender_id", sa.String(36)),
            sa.Column("province_value", sa.String(200)),
            sa.Column("district_value", sa.String(200)),
            sa.Column("municipality_value", sa.String(200)),
            sa.Column("reason", sa.String(100), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["raw_ingestion_id"], ["raw_ingestions.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(["tender_id"], ["tenders.id"], ondelete="SET NULL"),
        )
    for name, columns in [
        ("ix_geography_issue_source", ["source_id"]),
        ("ix_geography_issue_raw", ["raw_ingestion_id"]),
        ("ix_geography_issue_tender", ["tender_id"]),
    ]:
        if not _has_index("geography_resolution_issues", name):
            op.create_index(name, "geography_resolution_issues", columns)
    if not _has_table("notification_device_deliveries"):
        op.create_table(
            "notification_device_deliveries",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("notification_id", sa.String(36), nullable=False),
            sa.Column("device_token_id", sa.String(36)),
            sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("available_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("attempted_at", sa.DateTime(timezone=True)),
            sa.Column("submitted_at", sa.DateTime(timezone=True)),
            sa.Column("delivered_at", sa.DateTime(timezone=True)),
            sa.Column("error_code", sa.String(100)),
            sa.Column("error_message", sa.String(500)),
            sa.Column("provider_message_id", sa.String(255)),
            sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["device_token_id"], ["device_tokens.id"], ondelete="SET NULL"),
            sa.UniqueConstraint(
                "notification_id", "device_token_id", name="uq_notification_device_delivery"
            ),
        )
    for name, columns in [
        ("ix_notification_device_notification", ["notification_id"]),
        ("ix_notification_device_token", ["device_token_id"]),
        ("ix_notification_device_status", ["status", "available_at"]),
    ]:
        if not _has_index("notification_device_deliveries", name):
            op.create_index(name, "notification_device_deliveries", columns)
    op.execute("UPDATE notification_deliveries SET status='SUBMITTED' WHERE status='SENT'")
    if op.get_bind().dialect.name == "postgresql" and not _has_index(
        "saved_searches", "ix_saved_searches_filters_gin"
    ):
        op.create_index(
            "ix_saved_searches_filters_gin",
            "saved_searches",
            [sa.text("(filters::jsonb)")],
            postgresql_using="gin",
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql" and _has_index(
        "saved_searches", "ix_saved_searches_filters_gin"
    ):
        op.drop_index("ix_saved_searches_filters_gin", table_name="saved_searches")
    op.execute("UPDATE notification_deliveries SET status='SENT' WHERE status='SUBMITTED'")
    if _has_table("notification_device_deliveries"):
        op.drop_table("notification_device_deliveries")
    if _has_table("geography_resolution_issues"):
        op.drop_table("geography_resolution_issues")
    for column in ["signals", "match_method", "confidence"]:
        if _has_column("tender_duplicate_candidates", column):
            op.drop_column("tender_duplicate_candidates", column)
