"""
jwt_handler.py – JWT creation and verification.
Uses python-jose. Secret and algorithm come from Settings (never hardcoded).
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import get_settings

settings = get_settings()

# ── Password hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Token creation ───────────────────────────────────────────────────────────
def create_access_token(
    user_id: int,
    username: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


# ── Token verification ───────────────────────────────────────────────────────
def decode_access_token(token: str) -> dict:
    """
    Returns the decoded payload dict.
    Raises JWTError on invalid/expired tokens.
    """
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
