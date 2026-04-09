"""
auth_service.py – Business logic for authentication.
"""
from fastapi import HTTPException, status

from backend.auth.jwt_handler import hash_password, verify_password, create_access_token
from backend.repositories.user_repo import UserRepository
from backend.repositories.audit_repo import AuditRepository


class AuthService:

    @staticmethod
    def login(username: str, password: str, ip_address: str = None) -> dict:
        user = UserRepository.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )
        if not verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        token = create_access_token(
            user_id=user["id"],
            username=user["username"],
            role=user["role"],
        )
        AuditRepository.log(
            action="LOGIN",
            target_table="Users",
            target_id=user["id"],
            user_id=user["id"],
            ip_address=ip_address,
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user["id"],
            "username": user["username"],
            "role": user["role"],
        }

    @staticmethod
    def register(username: str, password: str, role: str) -> dict:
        existing = UserRepository.get_by_username(username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        hashed = hash_password(password)
        new_id = UserRepository.create(username, hashed, role)
        return {"user_id": new_id, "username": username, "role": role}
