from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from api.models import GroupRoleEnum, User, user_group_role_table
from api.security import create_access_token, hash_token


def create_user(test_db: Session):
    new_user = User(
        id=str(uuid4()),
        name="Asier",
        email="some@email.com",
        password=hash_token("1234"),
    )
    test_db.add(new_user)
    test_db.commit()
    return new_user


def test_user_requests_group_creation(client: TestClient, test_db: Session):
    user = create_user(test_db)
    headers = {"Authorization": f"JWT {create_access_token(user.id)}"}

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
    assert data["owner_id"] == user.id

    stmt = select(user_group_role_table).where(
        user_group_role_table.c.user_id == user.id,
        user_group_role_table.c.group_id == data["id"],
    )

    result = test_db.execute(stmt).first()

    assert result is not None
    assert result[2] == GroupRoleEnum.ADMIN.value
