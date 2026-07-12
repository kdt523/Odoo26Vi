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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.employee import Employee
from app.models.revoked_token import RevokedToken

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
    # Check if email already exists
    stmt = select(Employee).where(Employee.email == body.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        
    employee = Employee(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        role="Employee",
        status="Active"
    )
    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    return employee


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate credentials and return access + refresh JWT pair."""
    stmt = select(Employee).where(Employee.email == body.email)
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    
    if not employee or not verify_password(body.password, employee.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
    access_token = create_access_token(subject=str(employee.id), role=employee.role)
    refresh_token = create_refresh_token(subject=str(employee.id))
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Issue a new access token given a valid refresh token."""
    # Check if token is revoked
    revoked_stmt = select(RevokedToken).where(RevokedToken.token == body.refresh_token)
    revoked_res = await db.execute(revoked_stmt)
    if revoked_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
        
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
            
        subject = payload.get("sub")
        # In a real app we'd fetch the user to get their latest role.
        # For MVP, we'll extract it by fetching the DB.
        stmt = select(Employee).where(Employee.id == subject)
        result = await db.execute(stmt)
        employee = result.scalar_one_or_none()
        if not employee:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
            
        access_token = create_access_token(subject=str(employee.id), role=employee.role)
        new_refresh_token = create_refresh_token(subject=str(employee.id))
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Invalidate the given refresh token by storing it in a blocklist.
    Client is expected to discard the tokens on their end.
    """
    # Check if already revoked to be idempotent
    stmt = select(RevokedToken).where(RevokedToken.token == body.refresh_token)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        revoked = RevokedToken(token=body.refresh_token)
        db.add(revoked)
        await db.commit()
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
    return current_user
