"""Phase 0 schema
Revision ID: 0001
"""
from alembic import op
from app.core.database import Base
from app.models import *  # noqa
revision="0001"; down_revision=None; branch_labels=None; depends_on=None
PROVINCES=[("EC","Eastern Cape"),("FS","Free State"),("GP","Gauteng"),("KZN","KwaZulu-Natal"),("LP","Limpopo"),("MP","Mpumalanga"),("NC","Northern Cape"),("NW","North West"),("WC","Western Cape")]
def upgrade():
    bind=op.get_bind(); Base.metadata.create_all(bind)
    table=Base.metadata.tables["provinces"]
    op.bulk_insert(table,[{"id":f"00000000-0000-0000-0000-0000000000{i+1}","code":c,"name":n} for i,(c,n) in enumerate(PROVINCES)])
def downgrade(): Base.metadata.drop_all(op.get_bind())
