"""Add new default role Search

Revision ID: 7fb9546a6052
Revises: 0a6c4ced02cf
Create Date: 2024-09-18 23:38:03.831295

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fb9546a6052'
down_revision: Union[str, None] = '0a6c4ced02cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    roles_table = sa.table(
        'roles',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String)
    )

    op.bulk_insert(roles_table, [
        {'name': 'Search'}
    ]
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM roles WHERE name IN ('Search')")
    )
