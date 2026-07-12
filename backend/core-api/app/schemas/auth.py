"""
app/schemas/auth.py — Pydantic schemas for the auth router.

Note: SignupRequest intentionally does NOT expose a `role` field.
      Role is always set to 'Employee' at the service layer.
"""

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    # role is NOT exposed here — always Employee on signup


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class EmployeeOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    status: str
    department_id: str | None = None

    model_config = {"from_attributes": True}
