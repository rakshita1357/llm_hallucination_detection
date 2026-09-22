"""Authentication utilities for SkepticAI.

Provides password hashing, JWT token creation/validation,
and user authentication dependencies.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Backend.database.connection import get_session
from Backend.database.models import User
from Backend.database.repositories import UserRepository

# Password hashing context - use pbkdf2_sha256 to avoid bcrypt compatibility issues
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Security scheme
security = HTTPBearer(auto_error=False)


class TokenData:
    """Token payload data."""
    def __init__(self, user_id: str, email: str, exp: Optional[datetime] = None):
        self.user_id = user_id
        self.email = email
        self.exp = exp


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        exp_timestamp: int = payload.get("exp")
        if user_id is None or email is None:
            return None
        exp = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) if exp_timestamp else None
        return TokenData(user_id=user_id, email=email, exp=exp)
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """Get the current authenticated user from JWT token.

    Raises:
        HTTPException: 401 if token is missing, invalid, or user not found.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async with get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(token_data.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """Get the current user if authenticated, otherwise return None."""
    if credentials is None:
        return None
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        return None
    async with get_session() as session:
        user_repo = UserRepository(session)
        return await user_repo.get_by_id(token_data.user_id)