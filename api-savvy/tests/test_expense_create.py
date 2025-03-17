import datetime
from fastapi import status
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from api.models import Group, GroupRoleEnum, User, user_group_role_table
from api.security import create_access_token, hash_password


@pytest.fixture
def seed_admin(test_db: Session):
    new_user = User(
        id="1", name="Asier", email="some@email.com", password=hash_password("1234")
    )
    test_db.add(new_user)

    new_group = Group(id="group-id", name="Group 1", owner_id="1")
    test_db.add(new_group)

    test_db.execute(
        user_group_role_table.insert().values(
            user_id=new_user.id, group_id=new_group.id, role=GroupRoleEnum.ADMIN
        )
    )

    test_db.commit()
    test_db.refresh(new_user)
    return test_db


def test_user_cannot_create_expenses_in_non_existing_group(
    client: TestClient, seed_admin: Session
):
    headers = {"Authorization": f"JWT {create_access_token('1')}"}

    response = client.post(
        "/v1/groups/non-existing-group-id/expenses/",
        json={
            "name": "Expense 1",
            "amount": 15,
            "date": datetime.date.today().isoformat(),
        },
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == "Group not found"


@pytest.fixture
def seed_viewer(test_db: Session):
    new_user = User(
        id="1", name="Asier", email="some@email.com", password=hash_password("1234")
    )
    test_db.add(new_user)

    new_group = Group(id="group-id", name="Group 1", owner_id="1")
    test_db.add(new_group)

    test_db.execute(
        user_group_role_table.insert().values(
            user_id=new_user.id, group_id=new_group.id, role=GroupRoleEnum.VIEWER
        )
    )

    test_db.commit()
    test_db.refresh(new_user)
    return test_db


def test_user_cannot_create_expenses_due_to_insufficient_privileges(
    client: TestClient, seed_viewer: Session
):
    headers = {"Authorization": f"JWT {create_access_token('1')}"}

    response = client.post(
        "/v1/groups/group-id/expenses/",
        json={
            "name": "Expense 1",
            "amount": 15,
            "date": datetime.date.today().isoformat(),
        },
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert data["detail"] == "Insufficient privileges"


def test_user_creates_expense(client: TestClient, seed_admin: Session):
    headers = {"Authorization": f"JWT {create_access_token('1')}"}

    response = client.post(
        "/v1/groups/group-id/expenses/",
        json={
            "name": "Expense 1",
            "amount": 15,
            "date": datetime.date.today().isoformat(),
        },
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert data["id"] is not None
    assert data["name"] == "Expense 1"
    assert data["amount"] == 15
    assert data["category"] is None
    assert data["date"] == datetime.date.today().isoformat()
