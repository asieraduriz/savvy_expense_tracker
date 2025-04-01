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
    return refresh_token_obj, plain_refresh_token


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
    return refresh_token_obj, plain_refresh_token


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


def test_logout_success(
    client: TestClient, test_db: Session, test_user: User, valid_refresh_token: str
):
    refresh_token, refresh_token_str = valid_refresh_token
    refresh_token_before = (
        test_db.query(UserRefreshToken)
        .filter(
            UserRefreshToken.id == refresh_token.id,
            UserRefreshToken.revoked == False,
        )
        .first()
    )

    assert refresh_token_before is not None

    response = client.post(
        "/auth/logout",
        json={"token": refresh_token_str},
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Logout successful"

    refresh_token_after = (
        test_db.query(UserRefreshToken)
        .filter(
            UserRefreshToken.id == refresh_token_before.id,
        )
        .first()
    )
    assert refresh_token_after is not None
    assert refresh_token_after.revoked is True


def test_logout_invalid_refresh_token(client: TestClient):
    response = client.post(
        "/auth/logout",
        json={"token": "invalidtoken"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Invalid or already revoked refresh token"


def test_logout_refresh_token_does_not_exist(client: TestClient, test_user: User):
    nonexistent_refresh_token, _ = create_refresh_token(test_user.id + "invalid_suffix")
    response = client.post(
        "/auth/logout",
        json={"token": nonexistent_refresh_token},
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Invalid or already revoked refresh token"


def test_logout_expired_refresh_token(
    client: TestClient, expired_refresh_token, test_db: Session, test_user: User
):
    refresh_token, refresh_token_str = expired_refresh_token
    refresh_token_before = (
        test_db.query(UserRefreshToken)
        .filter(
            UserRefreshToken.id == refresh_token.id,
            UserRefreshToken.revoked == False,
        )
        .first()
    )
    assert refresh_token_before is not None

    response = client.post(
        "/auth/logout",
        json={"token": refresh_token_str},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Logout successful"

    refresh_token_after = (
        test_db.query(UserRefreshToken)
        .filter(
            UserRefreshToken.id == refresh_token_before.id,
        )
        .first()
    )
    assert refresh_token_after is not None
    assert refresh_token_after.revoked is True


def test_logout_already_revoked_refresh_token(
    client: TestClient, revoked_refresh_token: str
):
    response = client.post(
        "/auth/logout",
        json={"token": revoked_refresh_token},
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Invalid or already revoked refresh token"


def test_logout_empty_token_value(client: TestClient):
    response = client.post(
        "/auth/logout",
        json={"token": ""},
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Invalid or already revoked refresh token"
