import datetime
from fastapi import status
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from api.models import (
    Expense,
    ExpenseTypeEnum,
    Group,
    GroupRoleEnum,
    User,
    user_group_role_table,
)
from api.security import create_access_token, hash_password


@pytest.fixture
def seed_admin(test_db: Session):
    new_user = User(
        id="user-admin-id",
        name="Asier",
        email="admin@email.com",
        password=hash_password("1234"),
    )
    test_db.add(new_user)

    new_group = Group(id="group-admin-id", name="Admin Group", owner_id="user-admin-id")
    test_db.add(new_group)

    test_db.execute(
        user_group_role_table.insert().values(
            user_id=new_user.id, group_id=new_group.id, role=GroupRoleEnum.ADMIN
        )
    )

    test_db.commit()
    test_db.refresh(new_user)
    test_db.refresh(new_group)
    return new_user, new_group


def test_user_cannot_create_expenses_in_non_existing_group(
    client: TestClient, seed_admin: tuple[User, Group]
):
    admin_user, _ = seed_admin
    headers = {"Authorization": f"JWT {create_access_token(admin_user.id)}"}

    response = client.post(
        "/v1/groups/non-existing-group-id/expenses/",
        json={
            "name": "Expense 1",
            "amount": 15,
            "date": datetime.date.today().isoformat(),
            "expense_type": ExpenseTypeEnum.ONE_TIME.value,
        },
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == "Group not found"


@pytest.fixture
def seed_viewer(test_db: Session):
    new_user = User(
        id="user-viewer-id",
        name="Yana",
        email="viewer@email.com",
        password=hash_password("1234"),
    )
    test_db.add(new_user)

    new_group = Group(
        id="group-viewer-id", name="Viewer Group", owner_id="user-viewer-id"
    )
    test_db.add(new_group)

    test_db.execute(
        user_group_role_table.insert().values(
            user_id=new_user.id, group_id=new_group.id, role=GroupRoleEnum.VIEWER
        )
    )

    test_db.commit()
    test_db.refresh(new_user)
    test_db.refresh(new_group)
    return new_user, new_group


def test_user_cannot_create_expenses_due_to_insufficient_privileges(
    client: TestClient, seed_viewer: tuple[User, Group]
):
    viewer_user, viewer_group = seed_viewer
    headers = {"Authorization": f"JWT {create_access_token(viewer_user.id)}"}

    response = client.post(
        f"/v1/groups/{viewer_group.id}/expenses/",
        json={
            "name": "Expense 1",
            "amount": 15,
            "date": datetime.date.today().isoformat(),
            "expense_type": ExpenseTypeEnum.ONE_TIME.value,
        },
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert data["detail"] == "Insufficient privileges"


def test_user_creates_expense(
    client: TestClient, seed_admin: tuple[User, Group], test_db: Session
):
    admin_user, admin_group = seed_admin
    headers = {"Authorization": f"JWT {create_access_token(admin_user.id)}"}
    today = datetime.date.today()
    payload = {
        "name": "Expense 1",
        "amount": 15,
        "date": today.isoformat(),
        "expense_type": ExpenseTypeEnum.ONE_TIME.value,
    }

    response = client.post(
        f"/v1/groups/{admin_group.id}/expenses/", json=payload, headers=headers
    )

    data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert data["id"] is not None
    assert data["name"] == "Expense 1"
    assert data["amount"] == 15
    assert data["category"] is None
    assert data["date"] == today.isoformat()

    # Verify the expense was actually created in the database
    expense_from_db = test_db.query(Expense).filter_by(id=data["id"]).first()
    assert expense_from_db is not None
    assert expense_from_db.name == "Expense 1"
    assert expense_from_db.amount == 15
    assert expense_from_db.category is None
    assert expense_from_db.date == today
    assert expense_from_db.expense_type == ExpenseTypeEnum.ONE_TIME.value
    assert expense_from_db.creator_id == admin_user.id
    assert expense_from_db.group_id == admin_group.id
