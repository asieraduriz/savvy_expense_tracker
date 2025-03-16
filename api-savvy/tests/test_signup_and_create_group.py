from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session
from api.models import User
from api.security import create_access_token, hash_password

@pytest.fixture
def pre_populated_session(session: Session):
    new_user = User(id="1", name="Asier", email="some@email.com", password=hash_password("1234"))
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return session

def test_user_requests_group_creation(client: TestClient, pre_populated_session: Session):
    headers = {"Authorization": f"JWT {create_access_token('1')}"}

    response =client.post(
        "/v1/groups/",
        json={"name": "Group 1", "color": "red", "icon": "shopping-cart"},
        headers=headers
    )

    data = response.json()

    assert response.status_code == 201
    assert data["id"] is not None
