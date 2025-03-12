from pydantic import BaseModel

class SignupUser(BaseModel):
    name: str
    email: str
    password: str