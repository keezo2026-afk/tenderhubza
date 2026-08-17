"""Phase 1A connector state and acceptance metadata.
Revision ID: 0003
"""
from alembic import op
from app.core.database import Base
from app.models import *  # noqa
revision="0003";down_revision="0002";branch_labels=None;depends_on=None
def upgrade(): Base.metadata.create_all(op.get_bind())
def downgrade(): op.drop_table("connector_states")
