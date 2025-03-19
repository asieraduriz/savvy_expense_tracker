from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from api.models import User
from api.security import hash_password


def test_login_non_existing_user(client: TestClient):
    response = client.post(
        "/auth/login/", json={"email": "some@email.com", "password": "1234"}
    )
    data = response.json()

    assert response.status_code == 401
    assert data["detail"] == "Incorrect email or password"


@pytest.fixture
def pre_populated_session(test_db: Session):
    existing_user = User(
        name="Asier", email="some@email.com", password=hash_password("1234")
    )
    test_db.add(existing_user)
    test_db.commit()
    return test_db


def test_login_existing_user(client: TestClient, pre_populated_session: Session):
    response = client.post(
        "/auth/login/", json={"email": "some@email.com", "password": "1234"}
    )
    data = response.json()

    assert response.status_code == 200
    assert "id" not in data
    assert data["name"] == "Asier"
    assert data["email"] == "some@email.com"
    assert "password" not in data
    assert "access_token" in data


def test_login_existing_user_incorrect_password(
    client: TestClient, pre_populated_session: Session
):
    response = client.post(
        "/auth/login/", json={"email": "some@email.com", "password": "1235"}
    )
    data = response.json()

    assert response.status_code == 401
    assert data["detail"] == "Incorrect email or password"
