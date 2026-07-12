"""
app/routers/auth.py — Authentication router.

Endpoints:
  POST /signup      — Register a new Employee account (role is always Employee)
  POST /login       — Authenticate + issue JWT access + refresh tokens
  POST /refresh     — Refresh access token using a valid refresh token
  POST /logout      — Logout stub (client-side token discard)
  POST /forgot-password — Initiate password reset (stub)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    EmployeeOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    Role is hardcoded to 'Employee' — no client-supplied role accepted.
    """
    # TODO: check if email already exists → 409
    # TODO: create Employee(role="Employee", password_hash=hash_password(body.password))
    # TODO: flush & return created employee
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate credentials and return access + refresh JWT pair."""
    # TODO: fetch employee by email
    # TODO: verify_password(body.password, employee.password_hash) → 401 on failure
    # TODO: create_access_token(str(employee.id), employee.role)
    # TODO: create_refresh_token(str(employee.id))
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest):
    """Issue a new access token given a valid refresh token."""
    # TODO: decode_token(body.refresh_token), verify type == 'refresh'
    # TODO: issue new access_token + refresh_token
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user=Depends(get_current_user)):
    """
    Logout stub. JWT is stateless — real invalidation requires a token
    denylist (Redis recommended). Client should discard the token.
    TODO: implement token denylist if needed.
    """
    return None


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Initiate password reset flow.
    TODO: generate reset token, store expiry, send email via SMTP/SendGrid.
    """
    # Always return 202 to avoid email enumeration
    return {"detail": "If the email exists, a reset link has been sent."}


@router.get("/me", response_model=EmployeeOut)
async def get_me(current_user=Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    # TODO: return ORM employee object once get_current_user is wired
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
