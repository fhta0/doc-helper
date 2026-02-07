"""
API Dependencies
Common dependencies for API routes.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User


security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current authenticated user from JWT token, but allow unauthenticated access.

    Returns None if no token is provided or token is invalid.

    Args:
        credentials: Optional HTTP Bearer credentials
        db: Database session

    Returns:
        User object or None if not authenticated
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    return user


def reset_free_count_if_needed(user: User, db: Session) -> None:
    """
    Reset free count if it's a new month.

    Args:
        user: User object
        db: Database session
    """
    from datetime import date

    today = date.today()
    if user.last_reset_date is None or user.last_reset_date.month != today.month or user.last_reset_date.year != today.year:
        user.free_count = 3
        user.last_reset_date = today
        db.commit()


def check_count_available(user: User, check_type: str) -> str:
    """
    Check if user has available count for the check type.

    Args:
        user: User object
        check_type: Type of check ("basic" or "full")

    Returns:
        The cost type that will be used ("free", "basic", or "full")

    Raises:
        HTTPException: If no available count
    """
    if check_type == "full":
        # Full check only uses full_count
        if user.full_count <= 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="完整检测次数不足，请购买检测包",
            )
        return "full"
    else:  # basic
        # Basic check uses free_count first, then basic_count
        if user.free_count > 0:
            return "free"
        elif user.basic_count > 0:
            return "basic"
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="检测次数不足，请购买检测包",
            )
