"""
FastAPI dependency helpers.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db
from app.services.user import get_user_by_email

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
_oauth2_optional = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    subject = decode_access_token(token)
    if subject is None:
        raise _401
    user = await get_user_by_email(db, subject)
    if user is None or not user.is_active:
        raise _401
    return user


async def get_optional_user(
    token: str | None = Depends(_oauth2_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Returns the authenticated user, or None if no valid token is present."""
    if not token:
        return None
    subject = decode_access_token(token)
    if not subject:
        return None
    return await get_user_by_email(db, subject)
