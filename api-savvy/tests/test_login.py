from uuid import uuid4
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from api.models import User
from api.security import hask_token


@pytest.fixture
def user_fixture(test_db: Session):
    """Fixture to create a pre-populated user in the test database."""
    user = User(
        id=str(uuid4()),
        name="Asier",
        email="some@email.com",
        password=hask_token("1234"),
    )
    test_db.add(user)
    test_db.commit()
    return user


def test_login_non_existing_user(client: TestClient):
    """Test login with a non-existing user."""
    response = client.post(
        "/auth/login/", json={"email": "nonexistent@email.com", "password": "1234"}
    )
    data = response.json()

    assert response.status_code == 401
    assert data["detail"] == "Incorrect email or password"


def test_login_existing_user_success(client: TestClient, user_fixture: User):
    """Test successful login with an existing user."""
    response = client.post(
        "/auth/login/", json={"email": user_fixture.email, "password": "1234"}
    )
    data = response.json()

    assert response.status_code == 200
    assert "id" not in data  # Ensure id is not exposed
    assert data["name"] == user_fixture.name
    assert data["email"] == user_fixture.email
    assert "password" not in data  # Ensure password is not exposed
    assert "access_token" in data


def test_login_existing_user_incorrect_password(client: TestClient, user_fixture: User):
    """Test login with an existing user and incorrect password."""
    response = client.post(
        "/auth/login/",
        json={"email": user_fixture.email, "password": "wrong_password"},
    )
    data = response.json()

    assert response.status_code == 401
    assert data["detail"] == "Incorrect email or password"
