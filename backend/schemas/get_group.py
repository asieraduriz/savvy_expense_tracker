from typing import Optional
from pydantic import BaseModel

from backend.models.base import GroupStatus
from backend.schemas.user_response import UserResponse

class GroupResponse(BaseModel):
    id: str
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None
    created_by: UserResponse
    status: GroupStatus