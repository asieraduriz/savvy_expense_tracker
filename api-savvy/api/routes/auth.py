from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import uuid4

from api.database import get_db
from api.models import User
from api.security import create_access_token, hash_password, verify_password

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


@router.post("/signup/", status_code=201)
def signup(*, db: Session = Depends(get_db), user: UserSignup):
    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user is not None:
        raise HTTPException(status_code=409, detail={"duplicates": ["email"]})

    try:
        db_user = User(
            id=str(uuid4()),
            name=user.name,
            email=user.email,
            password=hash_password(user.password),
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return UserSignupResponse(
            id=db_user.id,
            name=db_user.name,
            email=db_user.email,
            access_token=create_access_token(db_user.id),
        )
    except Exception as e:
        print(e)


class UserLogin(BaseModel):
    email: str
    password: str


class UserLoginResponse(BaseModel):
    id: str
    name: str
    email: str
    access_token: str


@router.post("/login/", response_model=UserLoginResponse)
def login(*, db: Session = Depends(get_db), user: UserLogin):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return UserLoginResponse(
        id=db_user.id,
        name=db_user.name,
        email=db_user.email,
        access_token=create_access_token(db_user.id),
    )
