

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Header

from pydantic import BaseModel
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from uuid import uuid4

from api.database import get_session
from api.models import User
from api.security import create_access_token, get_user_from_auth, hash_password, verify_password

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
