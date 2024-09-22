"""add Last update date to db

Revision ID: 6461cc35d6e4
Revises: aa51dd51063b
Create Date: 2024-08-20 01:29:16.298775

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6461cc35d6e4'
down_revision = 'aa51dd51063b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание новой таблицы last_update_date
    op.create_table(
        'last_update_date',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('date', sa.DateTime, nullable=False)
    )


def downgrade() -> None:
    # Удаление таблицы last_update_date
    op.drop_table('last_update_date')
