from typing import Tuple
from fastapi import status
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from api.models import (
    Group,
    GroupInvitationStatusEnum,
    GroupRoleEnum,
    User,
    user_group_role_table,
)
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

    return new_first_user, new_second_user, new_group


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

    return new_first_user, new_second_user, new_group


@pytest.fixture
def seed_member_role_group(test_db: Session):
    new_first_user = User(
        id="100", name="Asier", email="some@email.com", password=b"1234"
    )
    new_second_user = User(
        id="200", name="Yana", email="other@email.com", password=b"1234"
    )

    new_group = Group(id="300", name="Group 1", owner_id="10", owner=new_first_user)
    test_db.add(new_first_user)
    test_db.add(new_second_user)
    test_db.add(new_group)

    test_db.execute(
        user_group_role_table.insert().values(
            user_id=new_first_user.id, group_id=new_group.id, role=GroupRoleEnum.MEMBER
        )
    )

    test_db.commit()
    test_db.refresh(new_first_user)
    test_db.refresh(new_second_user)
    test_db.refresh(new_group)

    return new_first_user, new_second_user, new_group


def test_user_cannot_invite_themselves(
    client: TestClient, seed_admin_role_group: Tuple[User, User, Group]
):
    first_user, _, _ = seed_admin_role_group
    headers = {"Authorization": f"JWT {create_access_token(first_user.id)}"}

    response = client.post(
        f"/v1/groups/3/invite/",
        json={"invitee_email": first_user.email},
        headers=headers,
    )

    response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_user_does_not_belong_to_group(
    client: TestClient, seed_admin_role_group: Tuple[User, User, Group]
):
    first_user, second_user, _ = seed_admin_role_group
    headers = {"Authorization": f"JWT {create_access_token(first_user.id)}"}

    response = client.post(
        f"/v1/groups/other-group-id/invite/",
        json={"invitee_email": second_user.email},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["detail"] == "User not in group"


def test_user_cannot_invite_non_existing_user(
    client: TestClient, seed_admin_role_group: Tuple[User, User, Group]
):
    first_user, _, _ = seed_admin_role_group
    headers = {"Authorization": f"JWT {create_access_token(first_user.id)}"}

    response = client.post(
        f"/v1/groups/3/invite/",
        json={
            "invitee_email": "non-existing-user-email",
        },
        headers=headers,
    )

    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == "Invitee not found"


def test_viewer_without_privileges_to_send_invitations(
    client: TestClient, seed_viewer_role_group: Tuple[User, User, Group]
):
    first_user, second_user, group = seed_viewer_role_group
    headers = {"Authorization": f"JWT {create_access_token(first_user.id)}"}

    response = client.post(
        f"/v1/groups/{group.id}/invite/",
        json={"invitee_email": second_user.email},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert data["detail"] == "Not enough privileges to invite"


def test_member_without_privileges_to_send_invitations(
    client: TestClient, seed_member_role_group: Tuple[User, User, Group]
):
    first_user, second_user, group = seed_member_role_group
    headers = {"Authorization": f"JWT {create_access_token(first_user.id)}"}

    response = client.post(
        f"/v1/groups/{group.id}/invite/",
        json={"invitee_email": second_user.email},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert data["detail"] == "Not enough privileges to invite"


@pytest.mark.parametrize("role", list(GroupRoleEnum))
def test_user_invites_existing_user(
    client: TestClient, seed_admin_role_group: Tuple[User, User, Group], role
):
    first_user, second_user, group = seed_admin_role_group
    headers = {"Authorization": f"JWT {create_access_token(first_user.id)}"}

    response = client.post(
        f"/v1/groups/{group.id}/invite/",
        json={
            "invitee_email": second_user.email,
            "role": role,
        },
        headers=headers,
    )

    data = response.json()

    assert response.status_code == 201
    assert data["id"] is not None
    assert data["group_id"] == group.id
    assert data["role"] == role
    assert data["status"] == GroupInvitationStatusEnum.PENDING
