"""create live search auto updates schedule table

Revision ID: 292230311e1f
Revises: 7fb9546a6052
Create Date: 2024-09-30 19:49:15.070153

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

AUTO_UPDATE_ENUM_NAME = 'autoupdatesmode'

# revision identifiers, used by Alembic.
revision: str = '292230311e1f'
down_revision: Union[str, None] = '7fb9546a6052'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('live_search_list_auto_update_schedule',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('list_id', sa.Integer(), nullable=False),
    sa.Column('mode', sa.Enum('Disabled', 'WeekDays', 'MonthDays', name=AUTO_UPDATE_ENUM_NAME), nullable=True),
    sa.Column('days', sa.String(length=100), nullable=True),
    sa.Column('hours', sa.Integer(), nullable=True),
    sa.Column('minutes', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['list_id'], ['live_search_list.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('live_search_list_auto_update_schedule')
    # ### end Alembic commands ###
    op.execute(f"DROP TYPE {AUTO_UPDATE_ENUM_NAME}")
