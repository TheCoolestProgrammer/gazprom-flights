"""add flight_id to Cargo

Revision ID: c7f2d3e4b5a6
Revises: b8d0ce7a59b0
Create Date: 2026-05-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7f2d3e4b5a6'
down_revision: Union[str, Sequence[str], None] = 'b8d0ce7a59b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('cargo_items', sa.Column('flight_id', sa.Integer(), sa.ForeignKey('flights.id'), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('cargo_items', 'flight_id')
