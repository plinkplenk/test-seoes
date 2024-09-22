"""add cascade

Revision ID: 4ef8930bfeb7
Revises: 1e6687648fb1
Create Date: 2024-08-28 23:12:13.491710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ef8930bfeb7'
down_revision: Union[str, None] = '1e6687648fb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Изменяем таблицу live_search_list_query для добавления каскадного удаления
    op.create_foreign_key(
        'fk_live_search_list_query_list_id_live_search_list',
        'live_search_list_query', 'live_search_list',
        ['list_id'], ['id'],
        ondelete='CASCADE'
    )

    # Изменяем таблицу query_live_search_yandex для добавления каскадного удаления
    op.create_foreign_key(
        'fk_query_live_search_yandex_query_live_search_list_query',
        'query_live_search_yandex', 'live_search_list_query',
        ['query'], ['id'],
        ondelete='CASCADE'
    )

    # Изменяем таблицу query_live_search_google для добавления каскадного удаления
    op.create_foreign_key(
        'fk_query_live_search_google_query_live_search_list_query',
        'query_live_search_google', 'live_search_list_query',
        ['query'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Восстанавливаем старые ограничения без каскадного удаления
    op.drop_constraint('fk_live_search_list_query_list_id_live_search_list', 'live_search_list_query', type_='foreignkey')
    op.create_foreign_key(
        'fk_live_search_list_query_list_id_live_search_list',
        'live_search_list_query', 'live_search_list',
        ['list_id'], ['id']
    )

    op.drop_constraint('fk_query_live_search_yandex_query_live_search_list_query', 'query_live_search_yandex', type_='foreignkey')
    op.create_foreign_key(
        'fk_query_live_search_yandex_query_live_search_list_query',
        'query_live_search_yandex', 'live_search_list_query',
        ['query'], ['id']
    )

    op.drop_constraint('fk_query_live_search_google_query_live_search_list_query', 'query_live_search_google', type_='foreignkey')
    op.create_foreign_key(
        'fk_query_live_search_google_query_live_search_list_query',
        'query_live_search_google', 'live_search_list_query',
        ['query'], ['id']
    )
