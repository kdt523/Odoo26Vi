"""
app/blueprints/notifications.py — Notifications blueprint.

Reads from the `notifications` table written by core-api.

Notification types:
  AssetAssigned | MaintenanceApproved | MaintenanceRejected |
  BookingCreated | BookingCancelled | TransferApproved |
  OverdueReturnAlert | AuditDiscrepancyFlagged

Endpoints:
  GET   /notifications          — List notifications for current user
  POST  /notifications/mark-read — Mark one or all notifications as read
"""

from flask import Blueprint, g, jsonify, request

from app.middleware.auth import require_jwt

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")

# Supported notification types (for documentation / future filtering)
NOTIFICATION_TYPES = [
    "AssetAssigned",
    "MaintenanceApproved",
    "MaintenanceRejected",
    "BookingCreated",
    "BookingCancelled",
    "TransferApproved",
    "OverdueReturnAlert",
    "AuditDiscrepancyFlagged",
]


@notifications_bp.get("/")
@require_jwt
def list_notifications():
    """
    List notifications for the authenticated user.

    Query params (implement later):
      - is_read: true | false
      - type: one of NOTIFICATION_TYPES
      - page / page_size

    TODO: get user_id from g.jwt_payload["sub"]
    TODO: SELECT * FROM notifications WHERE user_id = :user_id
          ORDER BY created_at DESC
          LIMIT :page_size OFFSET (:page - 1) * page_size
    """
    user_id = g.jwt_payload.get("sub") if g.jwt_payload else None
    return jsonify({
        "detail": "Not implemented",
        "user_id": user_id,
        "supported_types": NOTIFICATION_TYPES,
    }), 501


@notifications_bp.post("/mark-read")
@require_jwt
def mark_notifications_read():
    """
    Mark notifications as read.

    Request body:
      { "notification_ids": ["uuid", ...] }   — mark specific notifications
      { "all": true }                          — mark all for current user

    TODO: UPDATE notifications SET is_read = true
          WHERE user_id = :user_id
            AND (id = ANY(:ids) OR :all_flag = true)
    """
    body = request.get_json(silent=True) or {}
    return jsonify({"detail": "Not implemented", "body_received": body}), 501


@notifications_bp.get("/unread-count")
@require_jwt
def unread_count():
    """
    Return count of unread notifications for the current user.
    TODO: SELECT COUNT(*) FROM notifications WHERE user_id = :user_id AND is_read = false
    """
    return jsonify({"detail": "Not implemented", "unread_count": 0}), 501
