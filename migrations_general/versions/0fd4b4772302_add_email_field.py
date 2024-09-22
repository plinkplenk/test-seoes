"""add email field

Revision ID: 0fd4b4772302
Revises: 0c07329eada3
Create Date: 2024-09-14 00:50:53.937343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = '0fd4b4772302'
down_revision: Union[str, None] = '0c07329eada3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем новый столбец с временным уникальным значением по умолчанию
    op.add_column('user', sa.Column('email', sa.String(length=320), nullable=False, server_default='temporary'))

    # После добавления столбца убираем значение по умолчанию
    op.alter_column('user', 'email', server_default=None)

    # Получаем существующие записи и обновляем email для каждой записи
    conn = op.get_bind()
    
    # Выполняем SQL-запрос для получения данных
    users = conn.execute(text('SELECT id, username FROM "user"')).fetchall()

    # Обновляем email для каждой записи, делая его уникальным
    for user in users:
            unique_email = f"{user[1] or 'user'}_{user[0]}@example.com"  # user[1] - username, user[0] - id
            conn.execute(
                text('UPDATE "user" SET email = :email WHERE id = :id'),
                {'email': unique_email, 'id': user[0]}
            )

    # Создаем уникальный индекс на поле email
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)

def downgrade() -> None:
    # Удаляем индекс и столбец при откате миграции
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_column('user', 'email')
