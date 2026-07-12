"""
app/middleware/auth.py — JWT validation middleware for reports-api.

Validates the same JWT issued by core-api using the shared JWT_SECRET.
Provides a `require_jwt` decorator and `get_current_user_payload` helper.
"""

import os
from functools import wraps

from flask import g, jsonify, request
from jose import JWTError, jwt


def _get_secret():
    return os.getenv("JWT_SECRET", "change-me")


def _get_algorithm():
    return os.getenv("JWT_ALGORITHM", "HS256")


def decode_token(token: str) -> dict:
    """Decode and validate JWT; returns payload dict."""
    try:
        return jwt.decode(token, _get_secret(), algorithms=[_get_algorithm()])
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc


def get_current_user_payload() -> dict | None:
    """Return the decoded JWT payload stored on Flask's g, or None."""
    return getattr(g, "jwt_payload", None)


def require_jwt(f):
    """
    Decorator: extract + validate Bearer token from Authorization header.
    Sets g.jwt_payload on success; returns 401 on failure.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header.removeprefix("Bearer ").strip()
        try:
            g.jwt_payload = decode_token(token)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 401
        return f(*args, **kwargs)
    return decorated


def require_roles(*allowed_roles: str):
    """
    Decorator factory: validate JWT AND check role.
    Usage: @require_roles("Admin", "AssetManager")
    """
    def decorator(f):
        @wraps(f)
        @require_jwt
        def decorated(*args, **kwargs):
            payload = get_current_user_payload()
            role = payload.get("role", "") if payload else ""
            if role not in allowed_roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
