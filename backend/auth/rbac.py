"""
rbac.py – Role-Based Access Control dependency injectors for FastAPI.
Each get_current_* function is a FastAPI Depends() guard.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.jwt_handler import decode_access_token
from backend.repositories.audit_repo import AuditRepository

security = HTTPBearer()

VALID_ROLES = {"Admin", "Doctor", "Patient", "Pharmacist", "LabTech"}


class CurrentUser:
    """Lightweight user context extracted from JWT."""
    def __init__(self, user_id: int, username: str, role: str):
        self.user_id = user_id
        self.username = username
        self.role = role

    def __repr__(self) -> str:
        return f"<User id={self.user_id} role={self.role}>"


# ── Base dependency ───────────────────────────────────────────────────────────
async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> CurrentUser:
    from jose import JWTError
    try:
        payload = decode_access_token(credentials.credentials)
        user = CurrentUser(
            user_id=int(payload["sub"]),
            username=payload["username"],
            role=payload["role"],
        )
        # Attach to request state for middleware access
        request.state.current_user = user
        return user
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Role-specific guards ──────────────────────────────────────────────────────
def require_roles(*roles: str):
    """Factory: returns a Depends()-compatible coroutine for the given roles."""
    async def _guard(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted. Required role(s): {', '.join(roles)}",
            )
        return current_user
    return _guard


# Pre-built convenience guards
require_admin       = require_roles("Admin")
require_doctor      = require_roles("Doctor", "Admin")
require_pharmacist  = require_roles("Pharmacist", "Admin")
require_lab_tech    = require_roles("LabTech", "Admin")
require_patient     = require_roles("Patient", "Admin")
require_medical_staff = require_roles("Doctor", "Admin", "LabTech")
require_any_staff   = require_roles("Admin", "Doctor", "Pharmacist", "LabTech")
