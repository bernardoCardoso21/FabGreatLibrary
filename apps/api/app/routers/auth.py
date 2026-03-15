"""
Auth endpoints:
  POST /auth/register  — create account, receive tokens
  POST /auth/token     — login (OAuth2 password form), receive tokens
  POST /auth/refresh   — exchange refresh token for a new access token
  POST /auth/logout    — revoke refresh token
  GET  /auth/me        — return current user
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import (
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UpdatePreferencesRequest,
    UserResponse,
)
from app.services import auth as auth_svc
from app.services.user import (
    DuplicateEmailError,
    create_user,
    get_user_by_email,
    update_collection_mode,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
    description="Create a new user account and return a fresh access token and refresh token.",
    responses={409: {"description": "A user with that email address already exists."}},
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        user = await create_user(db, body.email, body.password)
    except DuplicateEmailError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    access_token = create_access_token(user.email)
    refresh = await auth_svc.create_refresh_token(db, user.id)
    await db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh.token)


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Login",
    description=(
        "Authenticate with email and password using the OAuth2 password flow. "
        "Returns a short-lived access token and a long-lived refresh token."
    ),
    responses={
        401: {"description": "Incorrect email or password."},
        403: {"description": "Account has been disabled."},
    },
)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await get_user_by_email(db, form.username)
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")

    access_token = create_access_token(user.email)
    refresh = await auth_svc.create_refresh_token(db, user.id)
    await db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh.token)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token",
    description=(
        "Exchange a valid refresh token for a new access token. "
        "The refresh token itself is reused (not rotated) unless it has expired or been revoked."
    ),
    responses={401: {"description": "Refresh token is invalid, expired, or has been revoked."}},
)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    rt = await auth_svc.use_refresh_token(db, body.refresh_token)
    if rt is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    access_token = create_access_token(rt.user.email)
    return TokenResponse(access_token=access_token, refresh_token=rt.token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Revoke the supplied refresh token. The access token will continue to work until it expires naturally.",
)
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> None:
    await auth_svc.revoke_refresh_token(db, body.refresh_token)
    await db.commit()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Current user profile",
    description="Return the profile of the currently authenticated user.",
)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update user preferences",
    description="Update the authenticated user's preferences (e.g. collection tracking mode).",
)
async def update_me(
    body: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    user = await update_collection_mode(db, current_user, body.collection_mode)
    await db.commit()
    return UserResponse.model_validate(user)
