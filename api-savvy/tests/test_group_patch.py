from uuid import uuid4
from fastapi import status
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from api.models import Group, GroupRoleEnum, User, user_group_role_table
from api.security import create_access_token, hask_token


def create_user(test_db: Session):
    new_user = User(
        id=str(uuid4()),
        name="Asier",
        email=f"{uuid4()}@email.com",
        password=hask_token("1234"),
    )
    test_db.add(new_user)
    test_db.commit()
    return new_user


def create_group(
    test_db: Session,
    user: User,
    role: GroupRoleEnum = GroupRoleEnum.ADMIN,
    name="Group 1",
    color="red",
    icon="shopping-cart",
):
    new_group = Group(
        id=str(uuid4()),
        name=name,
        color=color,
        icon=icon,
        owner=user,
    )
    test_db.add(new_group)
    test_db.commit()

    test_db.execute(
        user_group_role_table.insert().values(
            user_id=user.id, group_id=new_group.id, role=role.value
        )
    )

    test_db.commit()
    return new_group


def test_user_cannot_update_group_they_do_not_belong_to(
    client: TestClient, test_db: Session
):
    user = create_user(test_db)
    user_group = create_group(test_db, user)

    headers = {"Authorization": f"JWT {create_access_token(user.id)}"}

    response = client.patch(
        f"/v1/groups/other-{user_group.id}",
        json={"name": "New Name"},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == "Group not found"


def test_user_with_insufficient_role_cannot_update_group(
    client: TestClient, test_db: Session
):
    user = create_user(test_db)
    user_group = create_group(test_db, user, GroupRoleEnum.VIEWER)

    headers = {"Authorization": f"JWT {create_access_token(user.id)}"}

    response = client.patch(
        f"/v1/groups/{user_group.id}",
        json={"name": "New Name"},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert data["detail"] == "Insufficient privileges"


def test_user_sends_payload_that_is_the_same_as_current_group(
    client: TestClient, test_db: Session
):
    user = create_user(test_db)
    user_group = create_group(test_db, user)

    headers = {"Authorization": f"JWT {create_access_token(user.id)}"}

    response = client.patch(
        f"/v1/groups/{user_group.id}",
        json={
            "name": user_group.name,
            "color": user_group.color,
            "icon": user_group.icon,
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.text == ""


@pytest.mark.parametrize("name", ["New Name"])
@pytest.mark.parametrize("color", [None, "New Color"])
@pytest.mark.parametrize("icon", [None, "New Icon"])
def test_user_patches_group(client: TestClient, test_db: Session, name, color, icon):
    user = create_user(test_db)
    user_group = create_group(
        test_db, user, name="Group name", color="Group color", icon="Group icon"
    )

    headers = {"Authorization": f"JWT {create_access_token(user.id)}"}

    response = client.patch(
        f"/v1/groups/{user_group.id}",
        json={
            "name": name,
            "color": color,
            "icon": icon,
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == name
    assert data["color"] == color
    assert data["icon"] == icon

    test_db.query(Group).filter(Group.id == user_group.id).first()
    assert user_group.name == name
    assert user_group.color == color
    assert user_group.icon == icon
