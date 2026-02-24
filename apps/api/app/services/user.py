"""
User creation service.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models import User


class DuplicateEmailError(Exception):
    """Raised when a registration is attempted with an already-used email."""


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, email: str, password: str) -> User:
    """
    Create a new user.
    Raises DuplicateEmailError if the email is already registered.
    """
    if await get_user_by_email(session, email):
        raise DuplicateEmailError(f"Email already registered: {email}")

    user = User(email=email, hashed_password=hash_password(password))
    session.add(user)
    await session.flush()
    return user
