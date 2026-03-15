"""add collection_mode to users

Revision ID: a1b2c3d4e5f6
Revises: 977f7b0dd66e
Create Date: 2026-03-13 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '977f7b0dd66e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('collection_mode', sa.String(length=16), nullable=False, server_default='playset'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'collection_mode')
