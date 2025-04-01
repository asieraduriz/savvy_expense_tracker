from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import uuid4

from api.database import get_db
from api.iterable_operations import find_first
from api.models import User, UserRefreshToken
from api.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_token,
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
            password=hash_token(user.password),
        )

        refresh_token, refresh_token_expiry = create_refresh_token(db_user.id)

        db_refresh_token = UserRefreshToken(
            id=str(uuid4()),
            refresh_token=hash_token(refresh_token),
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

    refresh_token, expiry_timestamp = create_refresh_token(db_user.id)

    db_refresh_token = UserRefreshToken(
        id=str(uuid4()),
        refresh_token=hash_token(refresh_token),
        expiry_timestamp=expiry_timestamp,
        revoked=False,
        user=db_user,
    )

    db.add(db_refresh_token)
    db.commit()

    return UserAuthResponse(
        name=db_user.name,
        email=db_user.email,
        access_token=create_access_token(db_user.id),
        refresh_token=refresh_token,
    )


class RefreshTokenRequest(BaseModel):
    token: str


@router.post("/refresh/", response_model=UserAuthResponse)
def refresh_token(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    decoded_token = decode_refresh_token(body.token)
    decoded_user_id = decoded_token.get("sub")

    db_refresh_tokens = (
        db.query(UserRefreshToken)
        .filter(UserRefreshToken.user_id == decoded_user_id)
        .all()
    )
    print("All tokens", db_refresh_tokens)
    db_refresh_token = find_first(
        db_refresh_tokens, lambda x: verify_hash(body.token, x.refresh_token)
    )

    if db_refresh_token is None:
        print("Token not foundd")
        raise HTTPException(status_code=404, detail="Token not found")

    if db_refresh_token.revoked:
        raise HTTPException(status_code=401, detail="Token revoked")

    if db_refresh_token.expiry_timestamp < datetime.now(timezone.utc).date():
        db_refresh_token.revoked = True
        db.commit()
        raise HTTPException(status_code=401, detail="Token expired")

    if db_refresh_token.user is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    db_refresh_token.revoked = True

    new_refresh_token, new_refresh_token_expiry = create_refresh_token(
        db_refresh_token.user_id
    )
    db_refresh_token = UserRefreshToken(
        id=str(uuid4()),
        refresh_token=hash_token(new_refresh_token),
        expiry_timestamp=new_refresh_token_expiry,
        revoked=False,
        user=db_refresh_token.user,
    )
    db.add(db_refresh_token)

    db.commit()
    return UserAuthResponse(
        name=db_refresh_token.user.name,
        email=db_refresh_token.user.email,
        access_token=create_access_token(db_refresh_token.user_id),
        refresh_token=new_refresh_token,
    )
