from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session
from api.models import User
from api.security import decode_access_token, hash_password


def test_signup_user(client: TestClient):
    response =client.post(
        "/auth/signup/",
        json={"name": "Asier", "email": "some@email.com", "password": "1234"}
    )
    data = response.json()

    assert response.status_code == 201
    assert data["id"] is not None
    assert data["name"] == "Asier"
    assert data["email"] == "some@email.com"
    assert 'access_token' in data
    assert 'password' not in data
    assert decode_access_token(data['access_token'])['sub'] == data['id']

@pytest.fixture
def pre_populated_session(session: Session):
    existing_user = User(id="1", name="Asier", email="some@email.com", password=hash_password("1234"))
    session.add(existing_user)
    session.commit()
    return session

def test_signup_user_email_already_exists(client: TestClient, pre_populated_session: Session):
    response =client.post(
        "/auth/signup/",
        json={"name": "Asier", "email": "some@email.com", "password": "1234"}
    )
    data = response.json()

    assert response.status_code == 409
    assert data["detail"]["duplicates"] == ['email']