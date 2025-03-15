from typing import Optional
import bcrypt
import jwt
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status

SECRET_KEY = "048b99ae6407c7bc980fa7e3c5828547b7a947dfa7e0c7e80e6f85fd6c99ca33"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password


def verify_password(password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)


def create_access_token(user_id: Optional[int]) -> str:
    now_utc = datetime.now(timezone.utc)
    expire = now_utc + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, 'sub': user_id, 'type': 'access'}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# def create_refresh_token(user_id: str) -> str:
#     refresh_token = str(uuid.uuid4())
#     now_utc = datetime.now(timezone.utc)
#     expire = now_utc + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
#     payload = {
#         "sub": user_id,
#         "exp": expire,
#         "type": "refresh"
#     }
#     encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt


# def decode_refresh_token(refresh_token: str) -> dict:
#     try:
#         payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
#         if payload.get("type") != "refresh":
#             raise ValueError("Invalid token type")
#         return payload
#     except (jwt.PyJWTError, ValueError):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid refresh token",
#             headers={"WWW-Authenticate": "Bearer"},
#         )