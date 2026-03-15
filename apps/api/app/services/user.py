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
    """Look up a user by email address.

    Args:
        session: Active async database session.
        email: Email address to search for.

    Returns:
        The matching User, or None if no account exists with that email.
    """
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, email: str, password: str) -> User:
    """Create a new user account with a hashed password.

    Args:
        session: Active async database session.
        email: Email address for the new account. Must be unique.
        password: Plain-text password; stored as a bcrypt hash.

    Returns:
        The newly created User (flushed but not yet committed).

    Raises:
        DuplicateEmailError: If an account with the given email already exists.
    """
    if await get_user_by_email(session, email):
        raise DuplicateEmailError(f"Email already registered: {email}")

    user = User(email=email, hashed_password=hash_password(password))
    session.add(user)
    await session.flush()
    return user


async def update_collection_mode(
    session: AsyncSession, user: User, mode: str
) -> User:
    """Update the user's collection tracking mode.

    Args:
        session: Active async database session.
        user: The user whose preference to update.
        mode: Either 'master_set' or 'playset'.

    Returns:
        The updated User (flushed but not yet committed).
    """
    user.collection_mode = mode
    await session.flush()
    return user
