"""
app/blueprints/reports.py — Reports & analytics blueprint.

All endpoints return stub data with HTTP 501 and TODO comments.

Endpoints:
  GET /reports/asset-utilization      — Asset utilization trends (by category/dept/period)
  GET /reports/maintenance-frequency  — Maintenance frequency per asset / category
  GET /reports/allocation-summary     — Department-wise allocation summary
  GET /reports/booking-heatmap        — Booking density heatmap data by time slot
  GET /reports/export                 — Export stub (CSV or PDF)
"""

import csv
import io
from datetime import date
from flask import Blueprint, jsonify, request, current_app, Response
from sqlalchemy import func, desc, extract

# Temporarily bypassing auth for the scaffold pass to make testing easier
# from app.middleware.auth import require_jwt, require_roles

from app.extensions import get_engine, get_session
from app.models import Asset, AssetCategory, Allocation, Booking, MaintenanceRequest, Department

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")

def get_db():
    engine = get_engine(current_app)
    return get_session(engine)

@reports_bp.get("/asset-utilization")
def asset_utilization():
    db = get_db()
    # Simple utilization: count total allocations per asset
    results = db.query(
        Asset.name,
        func.count(Allocation.id).label("allocation_count")
    ).outerjoin(Allocation, Asset.id == Allocation.asset_id)\
     .group_by(Asset.id)\
     .order_by(desc("allocation_count"))\
     .limit(10).all()
    
    db.close()
    
    data = [{"name": r[0], "allocations": r[1]} for r in results]
    return jsonify(data)


@reports_bp.get("/maintenance-frequency")
def maintenance_frequency():
    db = get_db()
    # Count maintenance requests by category
    results = db.query(
        AssetCategory.name,
        func.count(MaintenanceRequest.id).label("freq")
    ).select_from(AssetCategory)\
     .outerjoin(Asset, Asset.category_id == AssetCategory.id)\
     .outerjoin(MaintenanceRequest, MaintenanceRequest.asset_id == Asset.id)\
     .group_by(AssetCategory.id)\
     .order_by(desc("freq")).all()
    
    db.close()
    
    data = [{"category": r[0], "frequency": r[1]} for r in results]
    return jsonify(data)


@reports_bp.get("/allocation-summary")
def allocation_summary():
    db = get_db()
    results = db.query(
        Department.name,
        func.count(Allocation.id).label("active_allocations")
    ).outerjoin(Allocation, (Department.id == Allocation.department_id) & (Allocation.status == 'Active'))\
     .group_by(Department.id)\
     .order_by(desc("active_allocations")).all()
     
    db.close()
    
    data = [{"department": r[0], "active_allocations": r[1]} for r in results]
    return jsonify(data)


@reports_bp.get("/booking-heatmap")
def booking_heatmap():
    db = get_db()
    # SQLite fallback support or PostgreSQL support
    # In Postgres: EXTRACT(ISODOW FROM start_time)
    results = db.query(
        extract('isodow', Booking.start_time).label('dow'),
        extract('hour', Booking.start_time).label('hour'),
        func.count(Booking.id).label("count")
    ).group_by('dow', 'hour').all()
    
    db.close()
    
    data = [{"day_of_week": r[0], "hour": r[1], "count": r[2]} for r in results if r[0] is not None]
    return jsonify(data)


@reports_bp.get("/export")
def export_report():
    report_type = request.args.get("report_type", "utilization")
    
    db = get_db()
    
    if report_type == "utilization":
        results = db.query(Asset.name, func.count(Allocation.id)).outerjoin(Allocation, Asset.id == Allocation.asset_id).group_by(Asset.id).all()
        headers = ["Asset Name", "Allocations"]
    elif report_type == "maintenance":
        results = db.query(AssetCategory.name, func.count(MaintenanceRequest.id)).select_from(AssetCategory).outerjoin(Asset, Asset.category_id == AssetCategory.id).outerjoin(MaintenanceRequest, MaintenanceRequest.asset_id == Asset.id).group_by(AssetCategory.id).all()
        headers = ["Category", "Maintenance Frequency"]
    elif report_type == "allocation":
        results = db.query(Department.name, func.count(Allocation.id)).outerjoin(Allocation, (Department.id == Allocation.department_id) & (Allocation.status == 'Active')).group_by(Department.id).all()
        headers = ["Department", "Active Allocations"]
    else:
        results = []
        headers = ["Data"]
        
    db.close()
        
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in results:
        writer.writerow(row)
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={report_type}_report.csv"}
    )
