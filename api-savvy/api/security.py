from typing import Literal
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.models import User

ALGORITHM = "HS256"
ACCESS_TOKEN_SECRET = "048b99ae6407c7bc980fa7e3c5828547b7a947dfa7e0c7e80e6f85fd6c99ca33"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

REFRESH_TOKEN_SECRET = "0fab5a909fd8c7d652edd6f7e15635f64bf1d00e354069052641c5549a91df1b"
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password


def verify_password(password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password)


def create_access_token(user_id: str) -> str:
    now_utc = datetime.now(timezone.utc)
    expire = now_utc + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    return _create_token(user_id, "access", ACCESS_TOKEN_SECRET, expire)

def create_refresh_token(user_id: str) -> str:
    now_utc = datetime.now(timezone.utc)
    expire = now_utc + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    return _create_token(user_id, "refresh", REFRESH_TOKEN_SECRET, expire)

def _create_token(user_id, type: Literal["access", "refresh"], secret: str, expire: datetime) -> str:
    to_encode = {"exp": expire, "sub": user_id, "type": type}
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    return _decode_token(token, 'access', ACCESS_TOKEN_SECRET)

def decode_refresh_token(token: str) -> dict:
    return _decode_token(token, 'refresh', REFRESH_TOKEN_SECRET)

def _decode_token(token, type: Literal["access", "refresh"], secret: str) -> dict:
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        if payload.get("type") != type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {type} token type: {payload.get('type')}"
            )
        return payload
    except jwt.PyJWTError:
        print("Raising 401 could not validate credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_from_auth(authorization: str, db: Session):
    if authorization is None or not authorization.startswith("JWT "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    token = authorization.split("JWT ")[1]
    payload = decode_access_token(token)
    user_id = payload.get("sub")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return user
