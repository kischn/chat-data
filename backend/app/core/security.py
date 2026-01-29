"""Security utilities for authentication."""
from datetime import datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        get_settings().app.secret_key,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode a JWT access token."""
    try:
        return jwt.decode(
            token,
            get_settings().app.secret_key,
            algorithms=["HS256"],
        )
    except Exception:
        return None
