from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from api.models import User
from api.security import create_access_token, hash_password


@pytest.fixture
def pre_populated_session(test_db: Session):
    new_user = User(
        id="1", name="Asier", email="some@email.com", password=hash_password("1234")
    )
    test_db.add(new_user)
    test_db.commit()
    test_db.refresh(new_user)
    return test_db


def test_user_requests_group_creation(
    client: TestClient, pre_populated_session: Session
):
    headers = {"Authorization": f"JWT {create_access_token('1')}"}

    response = client.post(
        "/v1/groups/",
        json={"name": "Group 1", "color": "red", "icon": "shopping-cart"},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == 201
    assert data["id"] is not None
    assert data["name"] == "Group 1"
    assert data["color"] == "red"
    assert data["icon"] == "shopping-cart"
    assert data["owner_id"] == "1"
