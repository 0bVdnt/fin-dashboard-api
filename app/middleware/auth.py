from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import decode_access_token
from app.database import get_db
from app.errors import UnauthorizedError
from app.errors.exceptions import InactiveAccountError
from app.models.user import User
from app.repositories.user_repository import UserRepository

# HTTPBearer extracts the token from "Authorization: Bearer <token>"
# auto_error=False in order to provide custome messages
bearer_schema = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_schema),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts and validates the JWT token,
    then returns the authenticated User object.

    Usage in handlers:
        @route.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            ...

    Raises:
        UnauthorizedError: If token is missing, invalid or expired
        InactiveAccountError: If the user's account is deactivated
    """

    # Check that a token was provided
    if credentials is None:
        raise UnauthorizedError("Authentication required - provide a Bearer token")

    # decode and validate JWT
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")

    # Extract user ID from token claims
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise UnauthorizedError("Invalid token - missing subject")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise UnauthorizedError("Invalid token - malformed subject")

    # Fetch the user from database to ensure they still exist and are active
    # This catches cases where a user is deleted or deactivated after token issuance
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        raise UnauthorizedError("User not found - account may have been deleted")

    if not user.is_active:
        raise InactiveAccountError()

    return user
