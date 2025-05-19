"""Add command metadata columns

Revision ID: 20250519_add_command_metadata_columns
Revises: <前回のリビジョンIDをここに>
Create Date: 2025-05-19 19:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250519_add_command_metadata_columns'
down_revision = '<前回のリビジョンIDをここに>'
branch_labels = None
depends_on = None

def upgrade():
    # ---- 新しい列を追加 ----
    op.add_column(
        'commands',
        sa.Column('issued_by', sa.String(length=16), nullable=False, server_default='user')
    )
    op.add_column(
        'commands',
        sa.Column('issued_reason', sa.Text(), nullable=True)
    )
    op.add_column(
        'commands',
        sa.Column('source_command_id', postgresql.UUID(), nullable=True)
    )
    op.add_column(
        'commands',
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5')
    )

def downgrade():
    # ---- 追加分を削除（ロールバック用） ----
    op.drop_column('commands', 'priority')
    op.drop_column('commands', 'source_command_id')
    op.drop_column('commands', 'issued_reason')
    op.drop_column('commands', 'issued_by')
