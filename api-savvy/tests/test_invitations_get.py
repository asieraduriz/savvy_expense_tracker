from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from api.models import (
    Group,
    GroupInvitation,
    GroupRoleEnum,
    User,
    user_group_role_table,
)
from api.security import create_access_token


@pytest.fixture
def seed_invitation(test_db: Session):
    new_first_user = User(
        id="1", name="Asier", email="some@email.com", password=b"1234"
    )
    new_second_user = User(
        id="2", name="Yana", email="other@email.com", password=b"1234"
    )

    new_group = Group(
        id="3", name="Group 1", owner_id=new_first_user.id, owner=new_first_user
    )
    new_other_group = Group(
        id="4", name="Group 2", owner_id=new_second_user.id, owner=new_second_user
    )
    test_db.add(new_first_user)
    test_db.add(new_second_user)
    test_db.add(new_group)
    test_db.add(new_other_group)

    test_db.commit()

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
    )

    new_other_invitation = GroupInvitation(
        id="5",
        group_id=new_other_group.id,
        emitter_id=new_second_user.id,
        invitee_id=new_first_user.id,
        role=GroupRoleEnum.MEMBER,
    )
    test_db.add(new_other_invitation)
    test_db.add(new_invitation)

    test_db.commit()

    return new_first_user, new_second_user, new_invitation, new_other_invitation


def test_user_gets_all_invitations__sent_and_received(
    client: TestClient,
    seed_invitation: tuple[User, User, GroupInvitation, GroupInvitation],
):
    user, _, invitation, other_invitation = seed_invitation
    headers = {"Authorization": f"JWT {create_access_token(user.id)}"}

    response = client.get("/v1/groups/invitations/", headers=headers)

    data = response.json()

    assert data is not None
    assert len(data) == 2
    assert data[0]["id"] == invitation.id
    assert data[1]["id"] == other_invitation.id


def test_user_gets_received_invitations(
    client: TestClient,
    seed_invitation: tuple[User, User, GroupInvitation, GroupInvitation],
):
    user, _, invitation, other_invitation = seed_invitation
    headers = {"Authorization": f"JWT {create_access_token(user.id)}"}

    response = client.get("/v1/groups/invitations/received", headers=headers)

    data = response.json()

    assert data is not None
    assert len(data) == 1
    assert data[0]["id"] == other_invitation.id


def test_user_gets_emitted_invitations(
    client: TestClient,
    seed_invitation: tuple[User, User, GroupInvitation, GroupInvitation],
):
    user, _, invitation, other_invitation = seed_invitation
    headers = {"Authorization": f"JWT {create_access_token(user.id)}"}

    response = client.get("/v1/groups/invitations/emitted", headers=headers)

    data = response.json()

    assert data is not None
    assert len(data) == 1
    assert data[0]["id"] == invitation.id
