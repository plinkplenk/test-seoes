"""add metrics type

Revision ID: 5a94ef525b78
Revises: 6461cc35d6e4
Create Date: 2024-08-20 16:14:10.873465

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a94ef525b78'
down_revision = '6461cc35d6e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавление нового столбца metrics_type в таблицу your_table_name
    op.add_column("last_update_date", sa.Column('metrics_type', sa.String(), nullable=False))


def downgrade() -> None:
    # Удаление столбца metrics_type из таблицы your_table_name
    op.drop_column("last_update_date", 'metrics_type')
