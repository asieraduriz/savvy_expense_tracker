from uuid import uuid4
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from api.models import User
from api.security import hash_password


def test_signup_user_success(client: TestClient):
    """Test successful user signup."""
    response = client.post(
        "/auth/signup/",
        json={"name": "Asier", "email": "newuser@email.com", "password": "1234"},
    )
    data = response.json()

    assert response.status_code == 201
    assert "id" not in data  # Ensure id is not exposed
    assert data["name"] == "Asier"
    assert data["email"] == "newuser@email.com"
    assert "access_token" in data
    assert "password" not in data


@pytest.fixture
def existing_user(test_db: Session):
    """Fixture to create an existing user in the test database."""
    user = User(
        id=str(uuid4()),
        name="Asier",
        email="existing@email.com",
        password=hash_password("1234"),
    )
    test_db.add(user)
    test_db.commit()
    return user


def test_signup_user_email_already_exists(client: TestClient, existing_user: User):
    """Test signup with an email that already exists."""
    response = client.post(
        "/auth/signup/",
        json={
            "name": "AnotherUser",
            "email": existing_user.email,
            "password": "password",
        },
    )
    data = response.json()

    assert response.status_code == 409
    assert data["detail"]["duplicates"] == ["email"]
