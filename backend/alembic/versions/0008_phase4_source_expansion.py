"""Phase 4 source expansion platform. Revision ID: 0008."""

from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def _tables():
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table):
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade():
    for name, column in [
        ("slug", sa.Column("slug", sa.String(200), unique=True)),
        ("procurement_url", sa.Column("procurement_url", sa.String(2048))),
        ("tender_url", sa.Column("tender_url", sa.String(2048))),
        ("province_id", sa.Column("province_id", sa.String(36), sa.ForeignKey("provinces.id"))),
        ("district_id", sa.Column("district_id", sa.String(36), sa.ForeignKey("districts.id"))),
        (
            "municipality_id",
            sa.Column("municipality_id", sa.String(36), sa.ForeignKey("municipalities.id")),
        ),
        ("status", sa.Column("status", sa.String(30), nullable=False, server_default="DISCOVERED")),
        ("priority", sa.Column("priority", sa.Integer(), nullable=False, server_default="5")),
        (
            "polling_interval_minutes",
            sa.Column(
                "polling_interval_minutes", sa.Integer(), nullable=False, server_default="1440"
            ),
        ),
        ("last_attempted_at", sa.Column("last_attempted_at", sa.DateTime(timezone=True))),
        (
            "last_tender_discovered_at",
            sa.Column("last_tender_discovered_at", sa.DateTime(timezone=True)),
        ),
        (
            "consecutive_failures",
            sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        ),
        ("last_error_category", sa.Column("last_error_category", sa.String(50))),
    ]:
        if name not in _columns("sources"):
            op.add_column("sources", column)
    if "documents_discovered" not in _columns("connector_runs"):
        op.add_column(
            "connector_runs",
            sa.Column("documents_discovered", sa.Integer(), nullable=False, server_default="0"),
        )
    if "error_category" not in _columns("connector_runs"):
        op.add_column("connector_runs", sa.Column("error_category", sa.String(50)))
    if "zero_result_anomaly" not in _columns("connector_runs"):
        op.add_column(
            "connector_runs",
            sa.Column(
                "zero_result_anomaly", sa.Boolean(), nullable=False, server_default=sa.false()
            ),
        )
    if "source_discoveries" not in _tables():
        op.create_table(
            "source_discoveries",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "source_id",
                sa.String(36),
                sa.ForeignKey("sources.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("discovered_by", sa.String(200), nullable=False),
            sa.Column("discovery_method", sa.String(50), nullable=False),
            sa.Column("evidence_url", sa.String(2048), nullable=False),
            sa.Column("notes", sa.Text()),
            sa.Column("verified_at", sa.DateTime(timezone=True)),
            sa.Column("verified_by", sa.String(200)),
            sa.Column(
                "verification_status", sa.String(30), nullable=False, server_default="DISCOVERED"
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_source_discoveries_source_id", "source_discoveries", ["source_id"])
    if "connector_registrations" not in _tables():
        op.create_table(
            "connector_registrations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "source_id",
                sa.String(36),
                sa.ForeignKey("sources.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("slug", sa.String(200), nullable=False, unique=True),
            sa.Column("version", sa.String(50), nullable=False),
            sa.Column("connector_type", sa.String(40), nullable=False),
            sa.Column("capabilities", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="REGISTERED"),
            sa.Column("implementation_reference", sa.String(500)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index(
            "ix_connector_registrations_source_id", "connector_registrations", ["source_id"]
        )
    if "municipality_source_coverage" not in _tables():
        op.create_table(
            "municipality_source_coverage",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "municipality_id",
                sa.String(36),
                sa.ForeignKey("municipalities.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("source_id", sa.String(36), sa.ForeignKey("sources.id", ondelete="SET NULL")),
            sa.Column("official_website_url", sa.String(2048)),
            sa.Column("source_identified", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("procurement_url", sa.String(2048)),
            sa.Column(
                "verification_status",
                sa.String(30),
                nullable=False,
                server_default="NOT_RESEARCHED",
            ),
            sa.Column("source_mechanism", sa.String(40)),
            sa.Column("connector_required", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column(
                "connector_implemented", sa.Boolean(), nullable=False, server_default=sa.false()
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index(
            "ix_municipality_coverage_source", "municipality_source_coverage", ["source_id"]
        )
    op.execute(
        "UPDATE sources SET slug='national-treasury-etender-ocds', status='ACTIVE', priority=1 WHERE connector_type='ETENDERS_OCDS'"
    )
    op.execute(
        "INSERT INTO connector_registrations(id,source_id,name,slug,version,connector_type,capabilities,status,implementation_reference,created_at,updated_at) SELECT '20000000-0000-0000-0000-000000000001',id,'National Treasury eTender OCDS','national-treasury-etenders-ocds','1.0.0','OCDS','{}','ACTIVE','app.connectors.national.etenders.ETendersConnector',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP FROM sources WHERE connector_type='ETENDERS_OCDS'"
    )


def downgrade():
    for table in ["municipality_source_coverage", "connector_registrations", "source_discoveries"]:
        op.drop_table(table)
    for column in ["zero_result_anomaly", "error_category", "documents_discovered"]:
        op.drop_column("connector_runs", column)
    for column in [
        "last_error_category",
        "consecutive_failures",
        "last_tender_discovered_at",
        "last_attempted_at",
        "polling_interval_minutes",
        "priority",
        "status",
        "municipality_id",
        "district_id",
        "province_id",
        "tender_url",
        "procurement_url",
        "slug",
    ]:
        op.drop_column("sources", column)
