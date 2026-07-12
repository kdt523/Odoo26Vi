"""add ReturnRequested to allocation_status_enum

Revision ID: a1b2c3d4e5f6
Revises: cfbd70859346
Create Date: 2026-07-12 11:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'cfbd70859346'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL does not allow ALTER TYPE ADD VALUE inside a transaction block.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE allocation_status_enum ADD VALUE IF NOT EXISTS 'ReturnRequested'")


def downgrade() -> None:
    # Removing a value from a Postgres ENUM is non-trivial and often not necessary for downgrades.
    pass
