from fastapi import APIRouter

from pydantic import BaseModel

router = APIRouter()


class UserSignup(BaseModel):
    name: str
    email: str
    password: str


class UserSignupResponse(BaseModel):
    id: str
    name: str
    email: str
    access_token: str
