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
    plain_refresh_token, _ = create_refresh_token(test_user.id)
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


def test_refresh_token_success(
    client: TestClient,
    test_db: Session,
    test_user: User,
    valid_refresh_token: tuple[str, str],
):
    plain_token, old_token_id = valid_refresh_token
    response = client.post(
        "/auth/refresh",
        json={"token": plain_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" not in data
    assert "password" not in data
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert "refresh_token" in data
    assert isinstance(data["refresh_token"], str)
    assert data["refresh_token"] != plain_token

    db_refresh_token = (
        test_db.query(UserRefreshToken)
        .filter(UserRefreshToken.id == old_token_id)
        .first()
    )
    assert db_refresh_token.revoked is True

    active_refresh_tokens = (
        test_db.query(UserRefreshToken)
        .filter(UserRefreshToken.user_id == test_user.id)
        .filter(UserRefreshToken.revoked == False)
        .count()
    )
    assert active_refresh_tokens == 1


def test_refresh_token_rotation(
    client: TestClient,
    test_db: Session,
    test_user: User,
    valid_refresh_token: tuple[str, str],
):
    plain_token, _ = valid_refresh_token

    response_success = client.post(
        "/auth/refresh",
        json={"token": plain_token},
    )
    assert response_success.status_code == 200

    response_fail = client.post(
        "/auth/refresh",
        json={"token": plain_token},
    )
    assert response_fail.status_code == 401
    data_fail = response_fail.json()
    assert "detail" in data_fail
    assert data_fail["detail"] == "Token revoked"


def test_refresh_token_empty_token_value(client: TestClient):
    response = client.post(
        "/auth/refresh",
        json={"token": ""},
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Could not validate credentials"


def test_refresh_token_user_does_not_exist(
    client: TestClient, test_db: Session, valid_refresh_token: tuple[str, str]
):
    plain_token, _ = valid_refresh_token

    test_db.query(User).filter(User.id == "1").delete()
    test_db.commit()

    response = client.post(
        "/auth/refresh",
        json={"token": plain_token},
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Invalid refresh token"
