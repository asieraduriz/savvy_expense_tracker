import datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status


from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import (
    Expense,
    ExpenseTypeEnum,
    GroupRoleEnum,
    SubscriptionExpense,
    SubscriptionFrequencyEnum,
    user_group_role_table,
)
from api.security import get_user_from_auth

router = APIRouter()


class ExpenseCreate(BaseModel):
    name: str
    amount: float
    category: Optional[str] = None
    date: datetime.date
    expense_type: ExpenseTypeEnum


class OneTimeExpenseCreate(ExpenseCreate):
    pass


class SubscriptionExpenseCreate(ExpenseCreate):
    on_every: int
    frequency: SubscriptionFrequencyEnum
    start_date: datetime.date
    end_date: Optional[datetime.date] = None


class ExpenseResponse(ExpenseCreate):
    id: str


class SubscriptionExpenseResponse(ExpenseResponse):
    on_every: int
    frequency: SubscriptionFrequencyEnum
    start_date: datetime.date
    end_date: Optional[datetime.date] = None


@router.post(
    "/groups/{group_id}/expenses/",
    status_code=status.HTTP_201_CREATED,
    response_model=ExpenseResponse | SubscriptionExpenseResponse,
)
def create_expense(
    group_id: str,
    expense: OneTimeExpenseCreate | SubscriptionExpenseCreate,
    db: Session = Depends(get_db),
    authorization: Annotated[str | None, Header()] = None,
):
    user = get_user_from_auth(authorization, db)
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
        new_expense = Expense(
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

        return ExpenseResponse(
            id=new_expense.id,
            name=new_expense.name,
            amount=new_expense.amount,
            category=new_expense.category,
            date=new_expense.date,
            expense_type=new_expense.expense_type,
        )

    if isinstance(expense, SubscriptionExpenseCreate):
        new_expense = SubscriptionExpense(
            name=expense.name,
            amount=expense.amount,
            category=expense.category,
            date=expense.date,
            creator=user,
            group_id=group_id,
            expense_type=expense.expense_type.value,
            on_every=expense.on_every,
            frequency=expense.frequency,
            start_date=expense.start_date,
            end_date=expense.end_date,
        )

        db.add(new_expense)
        db.commit()

        return SubscriptionExpenseResponse(
            id=new_expense.id,
            name=new_expense.name,
            amount=new_expense.amount,
            category=new_expense.category,
            date=new_expense.date,
            expense_type=new_expense.expense_type,
            on_every=new_expense.on_every,
            frequency=new_expense.frequency,
            start_date=new_expense.start_date,
            end_date=new_expense.end_date,
        )
