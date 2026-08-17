"""Phase 1 data engine, authentication, search and source bootstrap.
Revision ID: 0002
"""
from alembic import op
import sqlalchemy as sa
from app.core.database import Base
from app.models import *  # noqa
revision="0002";down_revision="0001";branch_labels=None;depends_on=None
SOURCE_ID="10000000-0000-0000-0000-000000000001"
def _add(table,name,column):
    inspector=sa.inspect(op.get_bind())
    if name not in {c["name"] for c in inspector.get_columns(table)}:op.add_column(table,column)
def upgrade():
    bind=op.get_bind();Base.metadata.create_all(bind)
    _add("raw_ingestions","request_url",sa.Column("request_url",sa.String(2048)))
    _add("raw_ingestions","http_status",sa.Column("http_status",sa.Integer()))
    _add("raw_ingestions","content_type",sa.Column("content_type",sa.String(255)))
    _add("raw_ingestions","response_timestamp",sa.Column("response_timestamp",sa.DateTime(timezone=True)))
    _add("raw_ingestions","payload_hash",sa.Column("payload_hash",sa.String(64)))
    _add("raw_ingestions","source_release_id",sa.Column("source_release_id",sa.String(255)))
    _add("raw_ingestions","ocds_identifier",sa.Column("ocds_identifier",sa.String(255)))
    for name,typ in [("source_release_id",sa.String(255)),("ocds_identifier",sa.String(255)),("payload_hash",sa.String(64)),("province_id",sa.String(36)),("district_id",sa.String(36)),("municipality_id",sa.String(36))]:_add("tenders",name,sa.Column(name,typ))
    _add("tenders","ingested_at",sa.Column("ingested_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    _add("tender_source_versions","change_summary",sa.Column("change_summary",sa.JSON(),nullable=False,server_default=sa.text("'{}'")))
    _add("districts","dataset_id",sa.Column("dataset_id",sa.String(36)))
    _add("municipalities","dataset_id",sa.Column("dataset_id",sa.String(36)))
    op.execute(sa.text("""INSERT INTO sources (id,name,source_type,organisation,website_url,api_url,active,connector_type,polling_frequency,created_at,updated_at)
      SELECT :id,'National Treasury eTender OCDS','NATIONAL','National Treasury of South Africa','https://www.etenders.gov.za','https://ocds-api.etenders.gov.za/api/OCDSReleases',true,'ETENDERS_OCDS','daily',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP
      WHERE NOT EXISTS (SELECT 1 FROM sources WHERE connector_type='ETENDERS_OCDS')""").bindparams(id=SOURCE_ID))
    if bind.dialect.name=="postgresql":
      op.execute("CREATE INDEX IF NOT EXISTS ix_raw_ingestions_payload_hash ON raw_ingestions (payload_hash)")
      op.execute("ALTER TABLE tenders ADD COLUMN IF NOT EXISTS search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(title,'') || ' ' || coalesce(description,'') || ' ' || coalesce(reference_number,'') || ' ' || coalesce(organisation,'') || ' ' || coalesce(municipality,'') || ' ' || coalesce(category,'') || ' ' || coalesce(contact_name,'') || ' ' || coalesce(contact_email,''))) STORED")
      op.execute("CREATE INDEX IF NOT EXISTS ix_tenders_search_vector ON tenders USING GIN (search_vector)")
      op.execute("CREATE INDEX IF NOT EXISTS ix_tenders_current_sort ON tenders (status, closing_date, issue_date)")
def downgrade():
    bind=op.get_bind()
    if bind.dialect.name=="postgresql":op.execute("DROP INDEX IF EXISTS ix_tenders_search_vector");op.execute("ALTER TABLE tenders DROP COLUMN IF EXISTS search_vector")
    op.execute(sa.text("DELETE FROM sources WHERE id=:id").bindparams(id=SOURCE_ID))
