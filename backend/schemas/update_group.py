from typing import Optional
from pydantic import BaseModel

class UpdateGroup(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
