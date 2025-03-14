from typing import Optional, Union
from pydantic import BaseModel
import datetime

from backend.models.base import Frequency

class BaseExpense(BaseModel):
    name: str
    amount: float
    category_name: Optional[str]
    category_color: Optional[str]
    category_icon: Optional[str]

class CraeteOneTimeExpense(BaseExpense):
    expense_type: str = 'one_time_expense'
    expense_date: datetime.datetime

class CreateSubscriptionExpense(BaseExpense):
    expense_type: str = 'subscription_expense'
    start_date: datetime.datetime
    end_date: Optional[datetime.datetime]
    every: int = 1
    frequency: Frequency = Frequency.MONTHLY

CreateExpense = Union[CraeteOneTimeExpense, CreateSubscriptionExpense]