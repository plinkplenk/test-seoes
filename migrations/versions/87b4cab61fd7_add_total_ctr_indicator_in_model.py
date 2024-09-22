"""add TOTAL_CTR indicator in model

Revision ID: 87b4cab61fd7
Revises: fe59ac7f0341
Create Date: 2024-07-15 11:55:43.216237

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '87b4cab61fd7'
down_revision = 'fe59ac7f0341'
branch_labels = None
depends_on = None


def upgrade():
    # Add new value to the existing 'indicator' enum
    op.execute("ALTER TYPE indicator ADD VALUE 'TOTAL_CTR'")

def downgrade():
    # Remove the added value from the 'indicator' enum
    pass
