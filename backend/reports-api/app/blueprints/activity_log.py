"""
app/blueprints/activity_log.py — Activity log blueprint.

Read-only access to the `activity_logs` table written by core-api.

Endpoints:
  GET /activity-log             — List activity log entries (filterable)
  GET /activity-log/{id}        — Single log entry detail
"""

from flask import Blueprint, g, jsonify, request

from app.middleware.auth import require_roles

activity_log_bp = Blueprint("activity_log", __name__, url_prefix="/api/activity-log")


@activity_log_bp.get("/")
@require_roles("Admin", "AssetManager")
def list_activity_logs():
    """
    List activity log entries.

    Query params (implement later):
      - user_id:     filter by actor
      - entity_type: e.g. 'Asset', 'Allocation', 'Booking'
      - entity_id:   filter by specific entity UUID
      - action:      e.g. 'asset.created', 'allocation.created'
      - from_date / to_date: filter by timestamp range
      - page / page_size

    TODO: build dynamic SQL WHERE clause from non-None params.
    TODO: ORDER BY timestamp DESC.
    TODO: return { items: [...], total: N, page: N, page_size: N }
    """
    filters = {
        "user_id": request.args.get("user_id"),
        "entity_type": request.args.get("entity_type"),
        "entity_id": request.args.get("entity_id"),
        "action": request.args.get("action"),
        "from_date": request.args.get("from_date"),
        "to_date": request.args.get("to_date"),
        "page": request.args.get("page", 1, type=int),
        "page_size": request.args.get("page_size", 20, type=int),
    }
    return jsonify({"detail": "Not implemented", "filters_received": filters}), 501


@activity_log_bp.get("/<log_id>")
@require_roles("Admin", "AssetManager")
def get_activity_log(log_id: str):
    """
    Fetch a single activity log entry by ID.
    TODO: SELECT * FROM activity_logs WHERE id = :log_id → 404 if not found
    """
    return jsonify({"detail": "Not implemented", "log_id": log_id}), 501
