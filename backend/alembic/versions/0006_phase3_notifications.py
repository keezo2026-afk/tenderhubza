"""Phase 3 notification domain.
Revision ID: 0006
"""
from alembic import op
import sqlalchemy as sa
from app.core.database import Base
from app.models import *  # noqa
revision="0006";down_revision="0005";branch_labels=None;depends_on=None
def _add(table,name,column):
 if name not in {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}:op.add_column(table,column)
def upgrade():
 Base.metadata.create_all(op.get_bind())
 _add("notification_deliveries","attempt_count",sa.Column("attempt_count",sa.Integer(),nullable=False,server_default="0"))
 _add("saved_searches","alerts_enabled",sa.Column("alerts_enabled",sa.Boolean(),nullable=False,server_default=sa.true()))
 _add("saved_tenders","closing_reminders_enabled",sa.Column("closing_reminders_enabled",sa.Boolean(),nullable=False,server_default=sa.true()))
 _add("saved_tenders","reminder_days",sa.Column("reminder_days",sa.JSON(),nullable=False,server_default=sa.text("'[7,3,1,0]'")))
def downgrade():
 for table in ["notification_deliveries","device_tokens","notifications","notification_preferences"]:op.drop_table(table)
 for table,column in [("saved_tenders","reminder_days"),("saved_tenders","closing_reminders_enabled"),("saved_searches","alerts_enabled")]:
  if column in {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}:op.drop_column(table,column)
