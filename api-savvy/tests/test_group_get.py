from uuid import uuid4
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from api.models import Group, GroupRoleEnum, User, user_group_role_table
from api.security import create_access_token, hash_password


def create_user(test_db: Session):
    new_user = User(
        id=str(uuid4()),
        name="Asier",
        email=f"{uuid4()}@email.com",
        password=hash_password("1234"),
    )
    test_db.add(new_user)
    test_db.commit()
    return new_user


def create_group(test_db: Session, user: User):
    new_group = Group(
        id=str(uuid4()),
        name="Group 1",
        color="red",
        icon="shopping-cart",
        owner=user,
    )
    test_db.add(new_group)
    test_db.commit()

    test_db.execute(
        user_group_role_table.insert().values(
            user_id=user.id, group_id=new_group.id, role=GroupRoleEnum.ADMIN
        )
    )

    test_db.commit()
    return new_group


def test_user_gets_groups_they_belong_to(client: TestClient, test_db: Session):
    user = create_user(test_db)
    user_group = create_group(test_db, user)

    other_user = create_user(test_db)
    other_user_group = create_group(test_db, other_user)
    headers = {"Authorization": f"JWT {create_access_token(user.id)}"}

    response = client.get(
        "/v1/groups/",
        headers=headers,
    )

    data = response.json()

    assert response.status_code == 200
    assert isinstance(data, list)
