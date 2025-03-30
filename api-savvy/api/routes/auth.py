from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import uuid4

from api.database import get_db
from api.models import User, UserRefreshToken
from api.security import (
    create_access_token,
    create_refresh_token,
    hask_token,
    verify_hash,
)

router = APIRouter()


class UserSignup(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserAuthResponse(BaseModel):
    name: str
    email: str
    access_token: str
    refresh_token: str


@router.post("/signup/", status_code=201, response_model=UserAuthResponse)
def signup(user: UserSignup, db: Session = Depends(get_db)):
    print("Signup", user)
    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user is not None:
        raise HTTPException(status_code=409, detail={"duplicates": ["email"]})

    try:
        db_user = User(
            id=str(uuid4()),
            name=user.name,
            email=user.email,
            password=hask_token(user.password),
        )

        refresh_token, refresh_token_expiry = create_refresh_token(db_user.id)

        db_refresh_token = UserRefreshToken(
            id=str(uuid4()),
            refresh_token=hask_token(refresh_token),
            expiry_timestamp=refresh_token_expiry,
            user=db_user,
        )
        db.add(db_user)
        db.add(db_refresh_token)
        db.commit()

        return UserAuthResponse(
            name=db_user.name,
            email=db_user.email,
            access_token=create_access_token(db_user.id),
            refresh_token=refresh_token,
        )
    except Exception as e:
        print(e)


@router.post("/login/", response_model=UserAuthResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_hash(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    return UserAuthResponse(
        name=db_user.name,
        email=db_user.email,
        access_token=create_access_token(db_user.id),
    )
