"""Phase 2 saved search chronological index.
Revision ID: 0005
"""
from alembic import op
import sqlalchemy as sa
revision="0005";down_revision="0004";branch_labels=None;depends_on=None
def upgrade():
 names={item["name"] for item in sa.inspect(op.get_bind()).get_indexes("saved_searches")}
 if "ix_saved_searches_user_created" not in names:op.create_index("ix_saved_searches_user_created","saved_searches",["user_id","created_at"])
def downgrade():
 names={item["name"] for item in sa.inspect(op.get_bind()).get_indexes("saved_searches")}
 if "ix_saved_searches_user_created" in names:op.drop_index("ix_saved_searches_user_created",table_name="saved_searches")
