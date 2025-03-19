from fastapi import Depends, Header
from sqlalchemy.orm import Session
from typing import Annotated

from api.database import get_db
from api.models import User
from api.security import get_user_from_auth


def get_authenticated_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> User:
    """Dependency to extract and authenticate the user from the authorization token."""
    user = get_user_from_auth(authorization, db)
    return user
