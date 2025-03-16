import pytest
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_user_from_auth,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from api.models import User

def test_hash_password():
    password = "testpassword"
    hashed_password = hash_password(password)
    assert isinstance(hashed_password, bytes)
    assert bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def test_verify_password():
    password = "testpassword"
    hashed_password = hash_password(password)
    assert verify_password(password, hashed_password)
    assert not verify_password("wrongpassword", hashed_password)

def test_create_access_token():
    user_id = "123"
    token = create_access_token(user_id)
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded_token["sub"] == user_id
    assert decoded_token["type"] == "access"
    assert "exp" in decoded_token

def test_decode_access_token():
    user_id = "123"
    token = create_access_token(user_id)
    decoded_token = decode_access_token(token)
    assert decoded_token["sub"] == user_id
    assert decoded_token["type"] == "access"
    assert "exp" in decoded_token

def test_decode_access_token_invalid_token():
    with pytest.raises(HTTPException) as excinfo:
        decode_access_token("invalidtoken")
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED

def test_decode_access_token_invalid_type():
    user_id = "123"
    now_utc = datetime.now(timezone.utc)
    expire = now_utc + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = jwt.encode({"exp": expire, 'sub': user_id, 'type': 'invalid'}, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(HTTPException) as excinfo:
        decode_access_token(token)
    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
    assert excinfo.value.detail == "Invalid token type"

def test_get_user_from_auth_valid(test_db: Session):
    user = User(id="123", name="Asier", email="test@example.com", password=b"hashed_password")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    token = create_access_token(user.id)
    authorization = f"JWT {token}"
    retrieved_user = get_user_from_auth(authorization, test_db)
    assert retrieved_user.id == user.id

def test_get_user_from_auth_invalid_token(test_db: Session):
    authorization = "JWT invalidtoken"
    with pytest.raises(HTTPException) as excinfo:
        get_user_from_auth(authorization, test_db)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_user_from_auth_user_not_found(test_db: Session):
    token = create_access_token("123")
    authorization = f"JWT {token}"
    with pytest.raises(HTTPException) as excinfo:
        get_user_from_auth(authorization, test_db)
    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND

def test_get_user_from_auth_no_authorization(test_db: Session):
    with pytest.raises(HTTPException) as excinfo:
        get_user_from_auth(None, test_db)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_user_from_auth_wrong_authorization_format(test_db: Session):
    with pytest.raises(HTTPException) as excinfo:
        get_user_from_auth("wrong format", test_db)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED