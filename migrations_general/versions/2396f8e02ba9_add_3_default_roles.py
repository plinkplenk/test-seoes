from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2396f8e02ba9'
down_revision = 'b522be0c9e66'
branch_labels = None
depends_on = None

def upgrade() -> None:
    roles_table = sa.table(
        'roles',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String)
    )

    op.bulk_insert(roles_table,
        [
            {'name': 'User'},
            {'name': 'Administrator'},
            {'name': 'Superuser'}
        ]
    )

def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM roles WHERE name IN ('User', 'Administrator', 'Superuser')")
    )
