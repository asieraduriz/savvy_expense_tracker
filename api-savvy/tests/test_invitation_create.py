from typing import Tuple
from fastapi import status
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from api.models import (
    Group,
    GroupInvitation,
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


@pytest.fixture
def seed_user_pending_invitation(test_db: Session):
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

    new_invitation = GroupInvitation(
        id="4",
        group_id=new_group.id,
        emitter_id=new_first_user.id,
        invitee_id=new_second_user.id,
        role=GroupRoleEnum.MEMBER,
        status=GroupInvitationStatusEnum.PENDING,
    )

    test_db.add(new_invitation)

    test_db.commit()

    return new_first_user, new_second_user, new_group, new_invitation


@pytest.fixture
def seed_user_already_accepted(test_db: Session):
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

    new_invitation = GroupInvitation(
        id="4",
        group_id=new_group.id,
        emitter_id=new_first_user.id,
        invitee_id=new_second_user.id,
        role=GroupRoleEnum.MEMBER,
        status=GroupInvitationStatusEnum.ACCEPTED,
    )

    test_db.execute(
        user_group_role_table.insert().values(
            user_id=new_second_user.id, group_id=new_group.id, role=new_invitation.role
        )
    )

    test_db.add(new_invitation)

    test_db.commit()

    return new_first_user, new_second_user, new_group, new_invitation


@pytest.fixture
def seed_user_already_accepted_but_left(test_db: Session):
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

    new_invitation = GroupInvitation(
        id="4",
        group_id=new_group.id,
        emitter_id=new_first_user.id,
        invitee_id=new_second_user.id,
        role=GroupRoleEnum.MEMBER,
        status=GroupInvitationStatusEnum.ACCEPTED,
    )

    test_db.add(new_invitation)

    test_db.commit()

    return new_first_user, new_second_user, new_group, new_invitation


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


def test_viewer_without_privileges_cannot_send_invitations(
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


def test_user_cannot_reinvite_other_with_pending_invitation(
    client: TestClient,
    seed_user_pending_invitation: tuple[User, User, Group, GroupInvitation],
):
    first_user, second_user, group, _ = seed_user_pending_invitation
    headers = {"Authorization": f"JWT {create_access_token(first_user.id)}"}

    response = client.post(
        f"/v1/groups/{group.id}/invite/",
        json={
            "invitee_email": second_user.email,
        },
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_409_CONFLICT
    assert data["detail"] == "Invitee already has a pending invitation"


def test_user_cannot_reinvite_other_user_in_same_group(
    client: TestClient,
    seed_user_already_accepted: tuple[User, User, Group, GroupInvitation],
):
    first_user, second_user, group, _ = seed_user_already_accepted
    headers = {"Authorization": f"JWT {create_access_token(first_user.id)}"}

    response = client.post(
        f"/v1/groups/{group.id}/invite/",
        json={
            "invitee_email": second_user.email,
        },
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_409_CONFLICT
    assert data["detail"] == "Invitee already in group"


def test_user_can_reinvite_if_other_user_not_in_group_even_if_previously_accepted_invitation(
    client: TestClient,
    seed_user_already_accepted_but_left: tuple[User, User, Group, GroupInvitation],
):
    first_user, second_user, group, invitation = seed_user_already_accepted_but_left
    headers = {"Authorization": f"JWT {create_access_token(first_user.id)}"}

    response = client.post(
        f"/v1/groups/{group.id}/invite/",
        json={
            "invitee_email": second_user.email,
        },
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert data["id"] != invitation.id
