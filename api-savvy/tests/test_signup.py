from uuid import uuid4
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from api.models import User, UserRefreshToken
from api.security import hask_token, verify_hash


def test_signup_user_success(client: TestClient, test_db: Session):
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
    assert "refresh_token" in data
    assert "password" not in data
    
    user = test_db.query(User).filter(
        User.email == "newuser@email.com"
    ).first()
    
    assert verify_hash(data["refresh_token"], user.refresh_tokens[0].refresh_token)
    assert user.refresh_tokens[0].revoked is False
    


@pytest.fixture
def existing_user(test_db: Session):
    """Fixture to create an existing user in the test database."""
    user = User(
        id=str(uuid4()),
        name="Asier",
        email="existing@email.com",
        password=hask_token("1234"),
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
