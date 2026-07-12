"""
app/models.py — Sync SQLAlchemy model mirrors for reports-api.

These are read-only mirrors of the tables owned by core-api.
Only tables/columns needed by reports-api blueprints are defined here.
Do NOT define relationships that require write access.
"""

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, Text, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions import Base


class Employee(Base):
    __tablename__ = "employees"
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255))
    email = Column(String(320))
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    role = Column(String(50))
    status = Column(String(50))


class Department(Base):
    __tablename__ = "departments"
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255))
    status = Column(String(50))


class AssetCategory(Base):
    __tablename__ = "asset_categories"
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255))


class Asset(Base):
    __tablename__ = "assets"
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255))
    asset_tag = Column(String(50))
    category_id = Column(UUID(as_uuid=True), ForeignKey("asset_categories.id"))
    status = Column(String(50))
    location = Column(String(512))
    is_bookable = Column(Boolean)


class Allocation(Base):
    __tablename__ = "allocations"
    id = Column(UUID(as_uuid=True), primary_key=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    allocated_date = Column(Date)
    expected_return_date = Column(Date)
    actual_return_date = Column(Date)
    status = Column(String(50))


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(UUID(as_uuid=True), primary_key=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    status = Column(String(50))


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"
    id = Column(UUID(as_uuid=True), primary_key=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    raised_by = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    priority = Column(String(50))
    status = Column(String(50))
    created_at = Column(DateTime(timezone=True))


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    type = Column(String(100))
    message = Column(Text)
    is_read = Column(Boolean)
    entity_type = Column(String(100))
    entity_id = Column(String(36))
    created_at = Column(DateTime(timezone=True))


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    action = Column(String(100))
    entity_type = Column(String(100))
    entity_id = Column(String(36))
    timestamp = Column(DateTime(timezone=True))
    details = Column(JSONB)
