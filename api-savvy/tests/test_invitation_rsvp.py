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
def seed_pending_invitation(test_db: Session):
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
        id="4", group_id="3", emitter_id="1", invitee_id="2", role=GroupRoleEnum.MEMBER
    )
    print("New invitation", new_invitation.status)
    test_db.add(new_invitation)

    test_db.commit()
    test_db.refresh(new_first_user)
    test_db.refresh(new_second_user)
    test_db.refresh(new_group)
    test_db.refresh(new_invitation)
    return test_db


def test_user_sends_rsvp_for_non_existing_invitation(
    client: TestClient, seed_pending_invitation: Session
):
    headers = {"Authorization": f"JWT {create_access_token('2')}"}

    response = client.post(
        f"/v1/groups/invitations/non-existing-invitation/rsvp/",
        json={"rsvp": GroupInvitationStatusEnum.REJECTED.value},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == "Invitation not found"


def test_user_rejects_invitation(client: TestClient, seed_pending_invitation: Session):
    headers = {"Authorization": f"JWT {create_access_token('2')}"}

    response = client.post(
        f"/v1/groups/invitations/4/rsvp/",
        json={"rsvp": GroupInvitationStatusEnum.REJECTED.value},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["id"] is not None
    assert data["group_id"] == "3"
    assert data["role"] == GroupRoleEnum.MEMBER
    assert data["status"] == GroupInvitationStatusEnum.REJECTED.value


def test_user_accepts_invitation(client: TestClient, seed_pending_invitation: Session):
    headers = {"Authorization": f"JWT {create_access_token('2')}"}

    response = client.post(
        f"/v1/groups/invitations/4/rsvp/",
        json={"rsvp": GroupInvitationStatusEnum.ACCEPTED.value},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["id"] is not None
    assert data["group_id"] == "3"
    assert data["role"] == GroupRoleEnum.MEMBER
    assert data["status"] == GroupInvitationStatusEnum.ACCEPTED.value

    fetch_one = seed_pending_invitation.execute(
        user_group_role_table.select().where(user_group_role_table.c.user_id == "2")
    ).fetchone()

    assert fetch_one is not None


@pytest.fixture
def seed_accepted_invitation(test_db: Session):
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
        group_id="3",
        emitter_id="1",
        invitee_id="2",
        role=GroupRoleEnum.MEMBER,
        status=GroupInvitationStatusEnum.ACCEPTED,
    )
    test_db.add(new_invitation)

    test_db.commit()
    test_db.refresh(new_first_user)
    test_db.refresh(new_second_user)
    test_db.refresh(new_group)
    test_db.refresh(new_invitation)
    return test_db


def test_user_cannot_update_after_rsvp_ing_invitation(
    client: TestClient, seed_accepted_invitation: Session
):
    headers = {"Authorization": f"JWT {create_access_token('2')}"}

    response = client.post(
        f"/v1/groups/invitations/4/rsvp/",
        json={"rsvp": GroupInvitationStatusEnum.ACCEPTED.value},
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_409_CONFLICT
    assert data["detail"] == "Invitation already rsvp'd"
