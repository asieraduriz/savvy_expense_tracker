from uuid import uuid4
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from api.models import Group, GroupRoleEnum, User, user_group_role_table
from api.security import create_access_token, hash_token


def create_user(test_db: Session):
    new_user = User(
        id=str(uuid4()),
        name="Asier",
        email=f"{uuid4()}@email.com",
        password=hash_token("1234"),
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


def test_user_cannot_get_non_existing_group(client: TestClient, test_db: Session):
    user = create_user(test_db)

    headers = {"Authorization": f"JWT {create_access_token(user.id)}"}

    response = client.get(
        f"/v1/groups/non-existing-group-id",
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_cannot_get_group_they_do_not_belong_to(
    client: TestClient, test_db: Session
):
    user = create_user(test_db)

    other_user = create_user(test_db)
    other_user_group = create_group(test_db, other_user)

    headers = {"Authorization": f"JWT {create_access_token(user.id)}"}

    response = client.get(
        f"/v1/groups/{other_user_group.id}",
        headers=headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_gets_groups_they_belong_to(client: TestClient, test_db: Session):
    user = create_user(test_db)
    user_group = create_group(test_db, user)

    headers = {"Authorization": f"JWT {create_access_token(user.id)}"}

    response = client.get(
        f"/v1/groups/{user_group.id}",
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["id"] == user_group.id
    assert data["name"] == user_group.name
    assert data["color"] == user_group.color
    assert data["icon"] == user_group.icon
    assert data["owner_id"] == user_group.owner_id
    assert data["owner_name"] == user_group.owner.name
