from typing import Optional
from pydantic import BaseModel

class UpdateGroup(BaseModel):
    name: Optional[str]
    color: Optional[str]
    icon: Optional[str]
