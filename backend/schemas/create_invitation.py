from typing import Optional
from pydantic import BaseModel

from backend.models.base import UserRole

class CreateInvitation(BaseModel):
    to_user_email: str
    group_id: str
    role: Optional[UserRole] = UserRole.MEMBER