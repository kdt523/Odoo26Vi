"""
app/__init__.py — Flask application factory for reports-api.

Usage:
  FLASK_APP=app flask run --port 8001

Or from Docker:
  flask run --host=0.0.0.0 --port=8001 --reload
"""

import os

from flask import Flask, jsonify
from flask_cors import CORS

from config import config_map
from app.blueprints.reports import reports_bp
from app.blueprints.notifications import notifications_bp
from app.blueprints.activity_log import activity_log_bp


def create_app(config_name: str | None = None) -> Flask:
    """Application factory — creates and configures the Flask app."""
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────────────────
    if config_name is None:
        config_name = os.getenv("ENVIRONMENT", "development")
    cfg = config_map.get(config_name, config_map["development"])
    app.config.from_object(cfg)

    # ── CORS ──────────────────────────────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": "*"}})  # TODO: restrict in production

    # ── Blueprints ────────────────────────────────────────────────────────
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(activity_log_bp)

    # ── Health check ──────────────────────────────────────────────────────
    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "reports-api"})

    # ── Error handlers ────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app
