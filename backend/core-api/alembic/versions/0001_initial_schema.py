"""Initial schema — all AssetFlow tables.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-12 00:00:00.000000

NOTE: This migration was hand-written for the scaffold pass.
      Run `alembic revision --autogenerate` after implementing any model
      changes to generate a proper auto-detected delta migration.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ──────────────────────────────────────────────────────────────
    department_status = postgresql.ENUM("Active", "Inactive", name="department_status_enum", create_type=False)
    employee_role = postgresql.ENUM("Employee", "DepartmentHead", "AssetManager", "Admin", name="employee_role_enum", create_type=False)
    employee_status = postgresql.ENUM("Active", "Inactive", name="employee_status_enum", create_type=False)
    asset_condition = postgresql.ENUM("New", "Good", "Fair", "Poor", "Damaged", name="asset_condition_enum", create_type=False)
    asset_status = postgresql.ENUM("Available", "Allocated", "Reserved", "UnderMaintenance", "Lost", "Retired", "Disposed", name="asset_status_enum", create_type=False)
    allocation_status = postgresql.ENUM("Active", "Returned", "TransferPending", "Transferred", name="allocation_status_enum", create_type=False)
    transfer_status = postgresql.ENUM("Requested", "Approved", "Rejected", "Reallocated", name="transfer_status_enum", create_type=False)
    booking_status = postgresql.ENUM("Upcoming", "Ongoing", "Completed", "Cancelled", name="booking_status_enum", create_type=False)
    maintenance_priority = postgresql.ENUM("Low", "Medium", "High", "Critical", name="maintenance_priority_enum", create_type=False)
    maintenance_status = postgresql.ENUM("Pending", "Approved", "Rejected", "TechnicianAssigned", "InProgress", "Resolved", name="maintenance_status_enum", create_type=False)
    audit_cycle_status = postgresql.ENUM("Draft", "Active", "Closed", name="audit_cycle_status_enum", create_type=False)
    audit_result = postgresql.ENUM("Verified", "Missing", "Damaged", name="audit_result_enum", create_type=False)
    notification_type = postgresql.ENUM(
        "AssetAssigned", "MaintenanceApproved", "MaintenanceRejected",
        "BookingCreated", "BookingCancelled", "TransferApproved",
        "OverdueReturnAlert", "AuditDiscrepancyFlagged",
        name="notification_type_enum", create_type=False
    )

    for e in [
        department_status, employee_role, employee_status, asset_condition,
        asset_status, allocation_status, transfer_status, booking_status,
        maintenance_priority, maintenance_status, audit_cycle_status,
        audit_result, notification_type,
    ]:
        e.create(op.get_bind(), checkfirst=True)

    # ── departments ────────────────────────────────────────────────────────
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("parent_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("head_employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", department_status, nullable=False, server_default="Active"),
        sa.ForeignKeyConstraint(["parent_department_id"], ["departments.id"], ondelete="SET NULL"),
    )

    # ── employees ─────────────────────────────────────────────────────────
    op.create_table(
        "employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(1024), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role", employee_role, nullable=False, server_default="Employee"),
        sa.Column("status", employee_status, nullable=False, server_default="Active"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_employees_email", "employees", ["email"])

    # Add deferred FK: departments.head_employee_id → employees.id
    op.create_foreign_key(
        "fk_dept_head", "departments", "employees",
        ["head_employee_id"], ["id"], ondelete="SET NULL",
    )

    # ── asset_categories ──────────────────────────────────────────────────
    op.create_table(
        "asset_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("custom_fields", postgresql.JSONB, nullable=False, server_default="{}"),
    )

    # ── assets ────────────────────────────────────────────────────────────
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_tag", sa.String(50), nullable=False, unique=True),
        sa.Column("serial_number", sa.String(255), nullable=True, unique=True),
        sa.Column("acquisition_date", sa.Date, nullable=True),
        sa.Column("acquisition_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("condition", asset_condition, nullable=False, server_default="New"),
        sa.Column("location", sa.String(512), nullable=True),
        sa.Column("is_bookable", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("status", asset_status, nullable=False, server_default="Available"),
        sa.Column("photo_ref", sa.String(1024), nullable=True),
        sa.Column("document_ref", sa.String(1024), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["asset_categories.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_assets_asset_tag", "assets", ["asset_tag"])

    # ── allocations ───────────────────────────────────────────────────────
    op.create_table(
        "allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("allocated_date", sa.Date, nullable=False),
        sa.Column("expected_return_date", sa.Date, nullable=True),
        sa.Column("actual_return_date", sa.Date, nullable=True),
        sa.Column("return_condition_notes", sa.Text, nullable=True),
        sa.Column("status", allocation_status, nullable=False, server_default="Active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_allocations_asset_id", "allocations", ["asset_id"])
    op.create_index("ix_allocations_employee_id", "allocations", ["employee_id"])

    # ── transfer_requests ─────────────────────────────────────────────────
    op.create_table(
        "transfer_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("allocation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("status", transfer_status, nullable=False, server_default="Requested"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["allocation_id"], ["allocations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by"], ["employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_by"], ["employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_employee_id"], ["employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_department_id"], ["departments.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_transfer_requests_allocation_id", "transfer_requests", ["allocation_id"])

    # ── bookings ──────────────────────────────────────────────────────────
    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", booking_status, nullable=False, server_default="Upcoming"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_bookings_asset_id", "bookings", ["asset_id"])
    op.create_index("ix_bookings_employee_id", "bookings", ["employee_id"])

    # ── maintenance_requests ──────────────────────────────────────────────
    op.create_table(
        "maintenance_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raised_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("issue_description", sa.Text, nullable=False),
        sa.Column("priority", maintenance_priority, nullable=False, server_default="Medium"),
        sa.Column("photo_ref", sa.String(1024), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("technician", sa.String(255), nullable=True),
        sa.Column("status", maintenance_status, nullable=False, server_default="Pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["raised_by"], ["employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_by"], ["employees.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_maintenance_requests_asset_id", "maintenance_requests", ["asset_id"])

    # ── audit_cycles ──────────────────────────────────────────────────────
    op.create_table(
        "audit_cycles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scope_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location", sa.String(512), nullable=True),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("status", audit_cycle_status, nullable=False, server_default="Draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["scope_department_id"], ["departments.id"], ondelete="SET NULL"),
    )

    # ── audit_cycle_auditors (join table) ─────────────────────────────────
    op.create_table(
        "audit_cycle_auditors",
        sa.Column("audit_cycle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("audit_cycle_id", "employee_id"),
        sa.ForeignKeyConstraint(["audit_cycle_id"], ["audit_cycles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
    )

    # ── audit_items ───────────────────────────────────────────────────────
    op.create_table(
        "audit_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("audit_cycle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("result", audit_result, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["audit_cycle_id"], ["audit_cycles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_audit_items_audit_cycle_id", "audit_items", ["audit_cycle_id"])
    op.create_index("ix_audit_items_asset_id", "audit_items", ["asset_id"])

    # ── notifications ─────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", notification_type, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["employees.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    # ── activity_logs ─────────────────────────────────────────────────────
    op.create_table(
        "activity_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["employees.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_activity_logs_user_id", "activity_logs", ["user_id"])
    op.create_index("ix_activity_logs_action", "activity_logs", ["action"])
    op.create_index("ix_activity_logs_timestamp", "activity_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_table("activity_logs")
    op.drop_table("notifications")
    op.drop_table("audit_items")
    op.drop_table("audit_cycle_auditors")
    op.drop_table("audit_cycles")
    op.drop_table("maintenance_requests")
    op.drop_table("bookings")
    op.drop_table("transfer_requests")
    op.drop_table("allocations")
    op.drop_table("assets")
    op.drop_table("asset_categories")

    # Remove FK before dropping employees/departments
    op.drop_constraint("fk_dept_head", "departments", type_="foreignkey")
    op.drop_table("employees")
    op.drop_table("departments")

    # Drop enums
    for enum_name in [
        "department_status_enum", "employee_role_enum", "employee_status_enum",
        "asset_condition_enum", "asset_status_enum", "allocation_status_enum",
        "transfer_status_enum", "booking_status_enum", "maintenance_priority_enum",
        "maintenance_status_enum", "audit_cycle_status_enum", "audit_result_enum",
        "notification_type_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
