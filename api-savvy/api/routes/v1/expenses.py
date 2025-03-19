import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status


from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import (
    ExpenseTypeEnum,
    GroupRoleEnum,
    OneTimeExpense,
    Subscription,
    SubscriptionCharge,
    SubscriptionFrequencyEnum,
    User,
    user_group_role_table,
)
from api.middlewares import get_authenticated_user

router = APIRouter()


class ExpenseCreate(BaseModel):
    name: str
    amount: float
    category: Optional[str] = None
    expense_type: ExpenseTypeEnum


class OneTimeExpenseCreate(ExpenseCreate):
    date: datetime.date


class SubscriptionExpenseCreate(ExpenseCreate):
    on_every: int
    frequency: SubscriptionFrequencyEnum
    start_date: datetime.date
    end_date: Optional[datetime.date] = None


class OneTimeExpenseResponse(ExpenseCreate):
    id: str
    name: str
    date: datetime.date


class SubscriptionExpenseResponse(ExpenseCreate):
    id: str
    on_every: int
    frequency: SubscriptionFrequencyEnum
    start_date: datetime.date
    end_date: Optional[datetime.date] = None


@router.post(
    "/groups/{group_id}/expenses/",
    status_code=status.HTTP_201_CREATED,
    response_model=OneTimeExpenseResponse | SubscriptionExpenseResponse,
)
def create_expense(
    group_id: str,
    expense: OneTimeExpenseCreate | SubscriptionExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_authenticated_user),
):
    stmt = select(user_group_role_table).where(
        user_group_role_table.c.user_id == user.id,
        user_group_role_table.c.group_id == group_id,
    )

    result = db.execute(stmt).first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )

    if result[2] not in [GroupRoleEnum.ADMIN, GroupRoleEnum.MEMBER]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient privileges",
        )

    if isinstance(expense, OneTimeExpenseCreate):
        new_expense = OneTimeExpense(
            name=expense.name,
            amount=expense.amount,
            category=expense.category,
            date=expense.date,
            creator=user,
            group_id=group_id,
            expense_type=expense.expense_type.value,
        )

        db.add(new_expense)
        db.commit()

        return OneTimeExpenseResponse(
            id=new_expense.id,
            name=new_expense.name,
            amount=new_expense.amount,
            category=new_expense.category,
            date=new_expense.date,
            expense_type=new_expense.expense_type,
        )

    if isinstance(expense, SubscriptionExpenseCreate):
        new_subscription = Subscription(
            name=expense.name,
            amount=expense.amount,
            category=expense.category,
            creator=user,
            group_id=group_id,
            expense_type=expense.expense_type.value,
            on_every=expense.on_every,
            frequency=expense.frequency,
            start_date=expense.start_date,
            end_date=expense.end_date,
        )

        db.add(new_subscription)
        db.commit()

        return SubscriptionExpenseResponse(
            id=new_subscription.id,
            name=new_subscription.name,
            amount=new_subscription.amount,
            category=new_subscription.category,
            expense_type=new_subscription.expense_type,
            on_every=new_subscription.on_every,
            frequency=new_subscription.frequency,
            start_date=new_subscription.start_date,
            end_date=new_subscription.end_date,
        )


class SubscriptionChargeCreate(BaseModel):
    amount: float
    date: datetime.date


class SubscriptionChargeCreateResponse(SubscriptionChargeCreate):
    id: str


@router.post(
    "/groups/{group_id}/subscriptions/{subscription_id}/charges/",
    status_code=status.HTTP_201_CREATED,
    response_model=SubscriptionChargeCreateResponse,
)
def create_subscription_charge(
    group_id: str,
    subscription_id: str,
    charge: SubscriptionChargeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_authenticated_user),
):
    stmt = select(user_group_role_table).where(
        user_group_role_table.c.user_id == user.id,
        user_group_role_table.c.group_id == group_id,
    )

    result = db.execute(stmt).first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )

    if result[2] not in [GroupRoleEnum.ADMIN, GroupRoleEnum.MEMBER]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient privileges",
        )

    db_subscription = (
        db.query(Subscription)
        .filter(Subscription.id == subscription_id)
        .filter(Subscription.group_id == group_id)
        .first()
    )

    if db_subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    new_charge = SubscriptionCharge(
        subscription=db_subscription,
        charged_date=charge.date,
        amount=charge.amount,
        creator=user,
    )

    db.add(new_charge)
    db.commit()

    return SubscriptionChargeCreateResponse(
        id=new_charge.id,
        amount=new_charge.amount,
        date=new_charge.charged_date,
    )
