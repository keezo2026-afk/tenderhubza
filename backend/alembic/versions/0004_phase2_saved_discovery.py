"""Phase 2 saved tenders and searches.
Revision ID: 0004
"""
from alembic import op
from app.core.database import Base
from app.models import *  # noqa
revision="0004";down_revision="0003";branch_labels=None;depends_on=None
def upgrade():Base.metadata.create_all(op.get_bind())
def downgrade():op.drop_table("saved_searches");op.drop_table("saved_tenders")
