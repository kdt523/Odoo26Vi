"""add next_maintenance_due_date and expected_retirement_date to assets

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('assets', sa.Column('next_maintenance_due_date', sa.Date(), nullable=True))
    op.add_column('assets', sa.Column('expected_retirement_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('assets', 'expected_retirement_date')
    op.drop_column('assets', 'next_maintenance_due_date')
