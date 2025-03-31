from uuid import uuid4
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session
from api.models import User, UserRefreshToken
from api.security import create_refresh_token, hash_token


# Fixture for creating a test user
@pytest.fixture
def test_user(test_db):
    user = User(
        id=1,
        username="testuser",
        email="test@email.com",
        hashed_password="hashedpassword",
    )
    test_db.add(user)
    test_db.commit()
    return user


# Fixture for creating a valid refresh token in the mock database
@pytest.fixture
def valid_refresh_token(test_db, test_user):
    plain_refresh_token = create_refresh_token(test_user.id)
    hashed_refresh_token = hash_token(plain_refresh_token)
    refresh_token_obj = UserRefreshToken(
        id=1,
        refresh_token=hashed_refresh_token,
        user_id=test_user.id,
        expiry_timestamp=datetime.now(timezone.utc) + timedelta(days=1),
        revoked=False,
        created_at=datetime.now(timezone.utc),
    )
    test_db.query(UserRefreshToken).filter(
        UserRefreshToken.user_id == test_user.id,
        UserRefreshToken.revoked == False,
        UserRefreshToken.expiry_timestamp > datetime.now(timezone.utc),
    ).first.return_value = refresh_token_obj
    return plain_refresh_token, refresh_token_obj.id


# Fixture for creating an expired refresh token in the mock database
@pytest.fixture
def expired_refresh_token(test_db, test_user):
    plain_refresh_token = create_refresh_token(
        subject=test_user.username, expires_delta=timedelta(days=-1)
    )
    hashed_refresh_token = hash_token(plain_refresh_token)
    refresh_token_obj = UserRefreshToken(
        id=2,
        refresh_token=hashed_refresh_token,
        user_id=test_user.id,
        expiry_timestamp=datetime.now(timezone.utc) + timedelta(days=-1),
        revoked=False,
        created_at=datetime.now(timezone.utc) - timedelta(days=2),
    )
    test_db.query(UserRefreshToken).filter(
        UserRefreshToken.user_id == test_user.id,
        UserRefreshToken.revoked == False,
        UserRefreshToken.expiry_timestamp <= datetime.now(timezone.utc),
    ).first.return_value = refresh_token_obj
    return plain_refresh_token


# Fixture for creating a revoked refresh token in the mock database
@pytest.fixture
def revoked_refresh_token(test_db, test_user):
    plain_refresh_token = create_refresh_token(
        subject=test_user.username,
        expires_delta=timedelta(days=0),
    )
    hashed_refresh_token = hash_token(plain_refresh_token)
    refresh_token_obj = UserRefreshToken(
        id=3,
        refresh_token=hashed_refresh_token,
        user_id=test_user.id,
        expiry_timestamp=datetime.now(timezone.utc) + timedelta(days=0),
        revoked=True,
        created_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    test_db.query(UserRefreshToken).filter(
        UserRefreshToken.user_id == test_user.id, UserRefreshToken.revoked == True
    ).first.return_value = refresh_token_obj
    return plain_refresh_token
