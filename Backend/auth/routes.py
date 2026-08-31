"""Authentication routes for SkepticAI.

Provides endpoints for user registration, login, and profile retrieval.
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Backend.database.connection import get_session
from Backend.database.models import User
from Backend.database.repositories import UserRepository
from Backend.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Request/Response models
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserProfile"


class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """Register a new user account."""
    async with get_session() as session:
        user_repo = UserRepository(session)

        # Check if email already exists
        existing_user = await user_repo.get_by_email(request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Validate password strength
        if len(request.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters",
            )

        # Create user
        hashed_password = hash_password(request.password)
        user = await user_repo.create(
            name=request.name,
            email=request.email,
            password_hash=hashed_password,
        )

        # Generate access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=timedelta(minutes=60 * 24 * 7),  # 7 days
        )

        return AuthResponse(
            access_token=access_token,
            user=UserProfile(
                id=str(user.id),
                name=user.name,
                email=user.email,
                role=user.role.value,
            ),
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Authenticate user and return access token."""
    async with get_session() as session:
        user_repo = UserRepository(session)

        user = await user_repo.get_by_email(request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=timedelta(minutes=60 * 24 * 7),  # 7 days
        )

        return AuthResponse(
            access_token=access_token,
            user=UserProfile(
                id=str(user.id),
                name=user.name,
                email=user.email,
                role=user.role.value,
            ),
        )


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's profile."""
    return UserProfile(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.value,
    )


@router.post("/logout")
async def logout():
    """Logout endpoint (client should discard token)."""
    return {"message": "Successfully logged out"}