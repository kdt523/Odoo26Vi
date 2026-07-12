"""add resolution fields to audit_items

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-12 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the enum type first
    audit_resolution_enum = sa.Enum(
        'confirm_lost', 'confirm_damaged_to_maintenance', 'override_verified',
        name='audit_resolution_enum'
    )
    audit_resolution_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('audit_items', sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('audit_items', sa.Column('resolved_action', audit_resolution_enum, nullable=True))
    op.add_column('audit_items', sa.Column('resolved_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('audit_items', 'resolved_notes')
    op.drop_column('audit_items', 'resolved_action')
    op.drop_column('audit_items', 'resolved')

    sa.Enum(name='audit_resolution_enum').drop(op.get_bind(), checkfirst=True)
