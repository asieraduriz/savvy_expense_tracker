import datetime
from uuid import uuid4
from fastapi import status
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from api.models import (
    Expense,
    ExpenseTypeEnum,
    Group,
    GroupRoleEnum,
    OneTimeExpense,
    Subscription,
    SubscriptionCharge,
    SubscriptionFrequencyEnum,
    User,
    user_group_role_table,
)
from api.security import create_access_token, hash_password


@pytest.fixture
def seed_admin(test_db: Session):
    new_user = User(
        id=str(uuid4()),
        name="Asier",
        email="admin@email.com",
        password=hash_password("1234"),
    )
    test_db.add(new_user)

    new_group = Group(id=str(uuid4()), name="Admin Group", owner_id=new_user.id)
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


def test_user_cannot_get_expenses_in_groupes_not_linked_to_them(
    client: TestClient, seed_admin: tuple[User, Group]
):
    admin_user, _ = seed_admin
    headers = {"Authorization": f"JWT {create_access_token(admin_user.id)}"}

    response = client.get(
        "/v1/groups/non-existing-group-id/expenses/",
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == "Group not found"


@pytest.fixture
def seed_member(test_db: Session):
    new_user = User(
        id=str(uuid4()),
        name="Yana",
        email="viewer@email.com",
        password=hash_password("1234"),
    )
    test_db.add(new_user)

    new_group = Group(id=str(uuid4()), name="Viewer Group", owner_id=new_user.id)

    new_expense = OneTimeExpense(
        id=str(uuid4()),
        name="Expense 1",
        category="Food",
        amount=15,
        date=datetime.date.today(),
        creator=new_user,
    )

    new_group.expenses.append(new_expense)

    new_subscription = Subscription(
        id=str(uuid4()),
        name="Subscription 1",
        category="Food",
        amount=15,
        start_date=datetime.date.today(),
        creator=new_user,
        on_every=1,
        frequency=SubscriptionFrequencyEnum.WEEKLY,
    )

    new_subscription_charge = SubscriptionCharge(
        id=str(uuid4()),
        amount=new_subscription.amount,
        charged_date=datetime.date.today(),
        subscription=new_subscription,
        creator=new_user,
    )
    new_subscription.charges.append(new_subscription_charge)
    new_group.expenses.append(new_subscription)
    test_db.add(new_group)

    test_db.execute(
        user_group_role_table.insert().values(
            user_id=new_user.id, group_id=new_group.id, role=GroupRoleEnum.ADMIN
        )
    )

    test_db.commit()
    test_db.refresh(new_user)
    test_db.refresh(new_group)
    return new_user, new_group, new_expense, new_subscription, new_subscription_charge


def test_user_gets_group_expenses(
    client: TestClient,
    seed_member: tuple[User, Group, OneTimeExpense, Subscription, SubscriptionCharge],
):
    user, group, expense, subscription, subscription_charge = seed_member
    headers = {"Authorization": f"JWT {create_access_token(user.id)}"}

    response = client.get(
        f"/v1/groups/{group.id}/expenses/",
        headers=headers,
    )

    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(data["expenses"], list)
    assert len(data["expenses"]) == 2
