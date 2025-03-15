from typing import Optional
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    id: Optional[str] = Field(index=True, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    password: bytes
