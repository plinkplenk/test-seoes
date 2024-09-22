"""delete user

Revision ID: aa51dd51063b
Revises: 67383e03317a
Create Date: 2024-08-01 18:32:35.065174

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aa51dd51063b'
down_revision = '67383e03317a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("user")


def downgrade() -> None:
    pass
