from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    name: str
    email: str
    password: str