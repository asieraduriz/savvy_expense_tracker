from fastapi import status
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from api.models import Group, GroupRoleEnum, User, user_group_role_table
from api.security import create_access_token


@pytest.fixture
def seed_admin_role_group(test_db: Session):
    new_first_user = User(
        id="1", name="Asier", email="some@email.com", password=b"1234"
    )
    new_second_user = User(
        id="2", name="Yana", email="other@email.com", password=b"1234"
    )

    new_group = Group(id="3", name="Group 1", owner_id="1", owner=new_first_user)
    test_db.add(new_first_user)
    test_db.add(new_second_user)
    test_db.add(new_group)

    test_db.execute(
        user_group_role_table.insert().values(
            user_id=new_first_user.id, group_id=new_group.id, role=GroupRoleEnum.ADMIN
        )
    )

    test_db.commit()
    test_db.refresh(new_first_user)
    test_db.refresh(new_second_user)
    test_db.refresh(new_group)
    return test_db


@pytest.fixture
def seed_viewer_role_group(test_db: Session):
    new_first_user = User(
        id="10", name="Asier", email="some@email.com", password=b"1234"
    )
    new_second_user = User(
        id="20", name="Yana", email="other@email.com", password=b"1234"
    )

    new_group = Group(id="30", name="Group 1", owner_id="10", owner=new_first_user)
    test_db.add(new_first_user)
    test_db.add(new_second_user)
    test_db.add(new_group)

    test_db.execute(
        user_group_role_table.insert().values(
            user_id=new_first_user.id, group_id=new_group.id, role=GroupRoleEnum.VIEWER
        )
    )

    test_db.commit()
    test_db.refresh(new_first_user)
    test_db.refresh(new_second_user)
    test_db.refresh(new_group)
    return test_db


def test_user_cannot_invite_themselves(client: TestClient, seed_admin_role_group):
    headers = {"Authorization": f"JWT {create_access_token('1')}"}
    print("Headers", headers)
    response = client.post(
        f"/v1/groups/3/invite/",
        json={"invitee_id": "1"},
        headers=headers,
    )

    response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_user_does_not_belong_to_group(client: TestClient, seed_admin_role_group):
    headers = {"Authorization": f"JWT {create_access_token('1')}"}

    response = client.post(
        f"/v1/groups/other-group-id/invite/",
        json={"invitee_id": "2"},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["detail"] == "User not in group"


def test_user_cannot_invite_non_existing_user(
    client: TestClient, seed_admin_role_group
):
    headers = {"Authorization": f"JWT {create_access_token('1')}"}

    response = client.post(
        f"/v1/groups/3/invite/",
        json={"invitee_id": "non-existing-user-id"},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == "Invitee not found"


def test_user_without_privileges_to_send_invitations(
    client: TestClient, seed_viewer_role_group
):
    headers = {"Authorization": f"JWT {create_access_token('10')}"}

    response = client.post(
        f"/v1/groups/30/invite/",
        json={"invitee_id": "20"},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert data["detail"] == "Not enough privileges to invite"


@pytest.mark.parametrize("role", list(GroupRoleEnum))
def test_user_invites_existing_user(client: TestClient, seed_admin_role_group, role):
    headers = {"Authorization": f"JWT {create_access_token('1')}"}

    response = client.post(
        f"/v1/groups/3/invite/",
        json={"invitee_id": "2", "role": role},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == 201
    assert data["id"] is not None
    assert data["group_id"] == "3"
    assert data["role"] == role
