"""
app/core/security.py — JWT utilities and role-based dependency stubs for core-api.

Actual password hashing/verification wiring and full validation are
marked as TODO — structure only for this scaffold pass.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import bcrypt
from jose import JWTError, jwt, ExpiredSignatureError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db import get_db
from app.models.employee import Employee

# ── Password hashing ───────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    # Hash password with bcrypt native directly to avoid passlib incompatibilities
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


# ── JWT ────────────────────────────────────────────────────────────────────
def create_access_token(subject: str, role: str, extra: Optional[dict] = None) -> str:
    """
    Issue a short-lived JWT.
    `subject` = employee_id (as string).
    `role`    = one of Employee | DepartmentHead | AssetManager | Admin.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "role": role, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": subject, "exp": expire, "type": "refresh"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT; raises HTTPException on failure."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ── HTTP Bearer extractor ──────────────────────────────────────────────────
bearer_scheme = HTTPBearer()


def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    return decode_token(credentials.credentials)


# ── Current-user dependency stub ───────────────────────────────────────────
async def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
):
    """
    Look up the Employee record from `payload["sub"]` in the DB.
    Return the Employee ORM object.
    """
    stmt = select(Employee).where(Employee.id == payload.get("sub"))
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
        
    return employee


# ── Role-based dependency factories ───────────────────────────────────────
def require_roles(*allowed_roles: str):
    """
    Dependency factory.  Usage:
        @router.get("/admin-only", dependencies=[Depends(require_roles("Admin"))])
    """
    async def _check(current_user=Depends(get_current_user)):
        # TODO: replace dict access with ORM attribute once get_current_user is wired
        role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
        if role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return _check


# Convenience shorthands
require_admin = require_roles("Admin")
require_asset_manager = require_roles("Admin", "AssetManager")
require_dept_head = require_roles("Admin", "AssetManager", "DepartmentHead")
require_authenticated = require_roles("Admin", "AssetManager", "DepartmentHead", "Employee")
