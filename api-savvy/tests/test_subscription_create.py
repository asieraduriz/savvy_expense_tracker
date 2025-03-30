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
    Subscription,
    User,
    user_group_role_table,
    SubscriptionFrequencyEnum,
)
from api.security import create_access_token, hask_token


@pytest.fixture
def seed_admin(test_db: Session):
    new_user = User(
        id="user-admin-id",
        name="Asier",
        email="admin@email.com",
        password=hask_token("1234"),
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


def test_user_cannot_create_subscriptions_in_non_existing_group(
    client: TestClient, seed_admin: tuple[User, Group]
):
    admin_user, _ = seed_admin
    headers = {"Authorization": f"JWT {create_access_token(admin_user.id)}"}

    response = client.post(
        "/v1/groups/non-existing-group-id/expenses/",
        json={
            "on_every": 1,
            "frequency": SubscriptionFrequencyEnum.WEEKLY.value,
            "amount": 15,
            "expense_type": ExpenseTypeEnum.SUBSCRIPTION.value,
            "start_date": datetime.date.today().isoformat(),
            "name": "Kombucha subscription",
        },
        headers=headers,
    )

    data = response.json()
    print(data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == "Group not found"


@pytest.fixture
def seed_viewer(test_db: Session):
    new_user = User(
        id="user-viewer-id",
        name="Yana",
        email="viewer@email.com",
        password=hask_token("1234"),
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


def test_user_cannot_create_subscriptions_due_to_insufficient_privileges(
    client: TestClient, seed_viewer: tuple[User, Group]
):
    viewer_user, viewer_group = seed_viewer
    headers = {"Authorization": f"JWT {create_access_token(viewer_user.id)}"}

    response = client.post(
        f"/v1/groups/{viewer_group.id}/expenses/",
        json={
            "amount": 15,
            "expense_type": ExpenseTypeEnum.SUBSCRIPTION.value,
            "start_date": datetime.date.today().isoformat(),
            "on_every": 1,
            "frequency": SubscriptionFrequencyEnum.WEEKLY.value,
            "name": "Kombucha subscription",
        },
        headers=headers,
    )

    data = response.json()
    print(data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert data["detail"] == "Insufficient privileges"


def test_user_creates_subscription(
    client: TestClient, seed_admin: tuple[User, Group], test_db: Session
):
    admin_user, admin_group = seed_admin
    headers = {"Authorization": f"JWT {create_access_token(admin_user.id)}"}
    today = datetime.date.today()
    payload = {
        "amount": 15,
        "expense_type": ExpenseTypeEnum.SUBSCRIPTION.value,
        "start_date": today.isoformat(),
        "category": "Kombucha",
        "name": "Kombucha subscription",
        "on_every": 1,
        "frequency": SubscriptionFrequencyEnum.WEEKLY.value,
    }

    response = client.post(
        f"/v1/groups/{admin_group.id}/expenses/", json=payload, headers=headers
    )

    data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert data["id"] is not None
    assert data["amount"] == 15
    assert data["expense_type"] == ExpenseTypeEnum.SUBSCRIPTION.value
    assert data["category"] == "Kombucha"
    assert data["on_every"] == 1
    assert data["frequency"] == SubscriptionFrequencyEnum.WEEKLY.value

    db_subscription = test_db.query(Subscription).filter_by(id=data["id"]).first()

    assert db_subscription is not None
    assert db_subscription.creator_id == admin_user.id
    assert db_subscription.group_id == admin_group.id
    assert db_subscription.category == "Kombucha"
    assert db_subscription.on_every == 1
    assert db_subscription.frequency == SubscriptionFrequencyEnum.WEEKLY.value
