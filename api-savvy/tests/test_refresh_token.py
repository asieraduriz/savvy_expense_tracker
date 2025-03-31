from uuid import uuid4
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session
from api.models import User, UserRefreshToken
from api.security import create_refresh_token, hash_token


@pytest.fixture
def test_user(test_db):
    user = User(
        id="1",
        name="User",
        email="test@email.com",
        password=hash_token("password"),
    )

    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def valid_refresh_token(test_db, test_user):
    plain_refresh_token = create_refresh_token(test_user.id)
    hashed_refresh_token = hash_token(plain_refresh_token)
    refresh_token_obj = UserRefreshToken(
        id="1",
        refresh_token=hashed_refresh_token,
        user_id=test_user.id,
        expiry_timestamp=datetime.now(timezone.utc) + timedelta(days=1),
        revoked=False,
        user=test_user,
    )

    test_db.add(refresh_token_obj)

    test_db.commit()
    return plain_refresh_token, refresh_token_obj.id


@pytest.fixture
def expired_refresh_token(test_db, test_user):
    plain_refresh_token, _ = create_refresh_token(test_user.id)
    hashed_refresh_token = hash_token(plain_refresh_token)
    refresh_token_obj = UserRefreshToken(
        id="2",
        refresh_token=hashed_refresh_token,
        user_id=test_user.id,
        expiry_timestamp=datetime.now(timezone.utc) + timedelta(days=-1),
        revoked=False,
        user=test_user,
    )

    test_db.add(refresh_token_obj)

    test_db.commit()
    return plain_refresh_token


@pytest.fixture
def revoked_refresh_token(test_db: Session, test_user: User):
    plain_refresh_token, _ = create_refresh_token(test_user.id)

    refresh_token_obj = UserRefreshToken(
        id="3",
        refresh_token=hash_token(plain_refresh_token),
        user_id=test_user.id,
        expiry_timestamp=datetime.now(timezone.utc) + timedelta(days=0),
        revoked=True,
        user=test_user,
    )

    test_db.add(refresh_token_obj)

    test_db.commit()
    return plain_refresh_token


def test_invalid_refresh_token(client: TestClient):
    response = client.post(
        "/auth/refresh",
        json={"token": "invalidtoken"},
    )

    assert response.status_code == 401


def test_refresh_token_does_not_exist_in_database(client: TestClient, test_user: User):
    refresh_token, _ = create_refresh_token(test_user.id)
    response = client.post(
        "/auth/refresh",
        json={"token": refresh_token},
    )

    assert response.status_code == 404


def test_refresh_token_is_revoked(client: TestClient, revoked_refresh_token: str):
    response = client.post(
        "/auth/refresh",
        json={"token": revoked_refresh_token},
    )

    data = response.json()
    assert response.status_code == 401
    assert data["detail"] == "Token revoked"


def test_refresh_token_is_expired(
    test_db: Session, client: TestClient, expired_refresh_token: str
):
    refresh_token = (
        test_db.query(UserRefreshToken).filter(UserRefreshToken.id == "2").first()
    )
    assert refresh_token.revoked == False
    response = client.post(
        "/auth/refresh",
        json={"token": expired_refresh_token},
    )

    data = response.json()
    assert response.status_code == 401
    assert data["detail"] == "Token expired"
    refresh_token = (
        test_db.query(UserRefreshToken).filter(UserRefreshToken.id == "2").first()
    )
    assert refresh_token.revoked == True
