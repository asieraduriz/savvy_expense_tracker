import datetime
from fastapi import status
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from api.models import (
    ExpenseTypeEnum,
    Group,
    GroupRoleEnum,
    Subscription,
    SubscriptionFrequencyEnum,
    User,
    SubscriptionCharge,
    user_group_role_table,
    SubscriptionFrequencyEnum,
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

    new_subscription = Subscription(
        on_every=1,
        frequency=SubscriptionFrequencyEnum.MONTHLY,
        start_date=datetime.date.today(),
        creator=new_user,
        group=new_group,
        category="Kombucha",
        name="Kombucha subscription",
        amount=15,
    )

    test_db.add(new_subscription)

    test_db.commit()
    test_db.refresh(new_user)
    test_db.refresh(new_group)
    test_db.refresh(new_subscription)
    return new_user, new_group, new_subscription


def test_user_cannot_create_subscription_charges_in_non_existing_group(
    client: TestClient, seed_admin
):
    admin_user, _, __ = seed_admin
    headers = {"Authorization": f"JWT {create_access_token(admin_user.id)}"}

    response = client.post(
        "/v1/groups/non-existing-group-id/subscriptions/subscription-id/charges",
        json={
            "amount": 15,
            "date": datetime.date.today().isoformat(),
        },
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == "Group not found"


def test_user_cannot_create_subscription_charges_in_non_existing_subscription(
    client: TestClient, seed_admin: tuple[User, Group, Subscription]
):
    admin_user, admin_group, _ = seed_admin
    headers = {"Authorization": f"JWT {create_access_token(admin_user.id)}"}

    response = client.post(
        f"/v1/groups/{admin_group.id}/subscriptions/non-existing-subscription-id/charges",
        json={
            "amount": 15,
            "date": datetime.date.today().isoformat(),
        },
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == "Subscription not found"


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

    new_subscription = Subscription(
        on_every=1,
        frequency=SubscriptionFrequencyEnum.MONTHLY,
        start_date=datetime.date.today(),
        creator=new_user,
        group=new_group,
        category="Kombucha",
        name="Kombucha subscription",
        amount=15,
    )

    test_db.add(new_subscription)

    test_db.commit()
    test_db.refresh(new_user)
    test_db.refresh(new_group)
    test_db.refresh(new_subscription)
    return new_user, new_group, new_subscription


def test_user_cannot_create_subscription_charges_due_to_insufficient_privileges(
    client: TestClient, seed_viewer: tuple[User, Group, Subscription]
):
    viewer_user, viewer_group, viewer_subscription = seed_viewer

    headers = {"Authorization": f"JWT {create_access_token(viewer_user.id)}"}

    response = client.post(
        f"/v1/groups/{viewer_group.id}/subscriptions/{viewer_subscription.id}/charges",
        json={
            "amount": 15,
            "date": datetime.date.today().isoformat(),
        },
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert data["detail"] == "Insufficient privileges"


def test_user_creates_subscription_charge(
    client: TestClient, seed_admin: tuple[User, Group, Subscription], test_db: Session
):
    admin_user, admin_group, admin_subscription = seed_admin
    headers = {"Authorization": f"JWT {create_access_token(admin_user.id)}"}
    today = datetime.date.today()
    payload = {
        "amount": 15,
        "date": today.isoformat(),
        "expense_type": ExpenseTypeEnum.SUBSCRIPTION.value,
        "start_date": today.isoformat(),
        "category": "Kombucha",
        "on_every": 1,
        "frequency": SubscriptionFrequencyEnum.WEEKLY.value,
    }

    response = client.post(
        f"/v1/groups/{admin_group.id}/subscriptions/{admin_subscription.id}/charges/",
        json=payload,
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert data["id"] is not None
    assert data["amount"] == 15
    assert data["date"] == today.isoformat()

    db_subscription_charge = (
        test_db.query(SubscriptionCharge).filter_by(id=data["id"]).first()
    )
    assert db_subscription_charge is not None
    assert db_subscription_charge.amount == 15
    assert db_subscription_charge.creator_id == admin_user.id
    assert db_subscription_charge.subscription_id == admin_subscription.id
