from typing import Optional
from pydantic import BaseModel

class CreateGroup(BaseModel):
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None