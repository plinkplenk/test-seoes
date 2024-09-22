from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '90cf6df62c39'
down_revision = '2396f8e02ba9'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Добавляем значение по умолчанию для колонки role
    op.alter_column(
        'user',  # Имя таблицы
        'role',  # Имя колонки
        existing_type=sa.Integer,
        server_default='1'  # Значение по умолчанию
    )

def downgrade() -> None:
    # Удаляем значение по умолчанию для колонки role
    op.alter_column(
        'user',  # Имя таблицы
        'role',  # Имя колонки
        existing_type=sa.Integer,
        server_default=None  # Убираем значение по умолчанию
    )
