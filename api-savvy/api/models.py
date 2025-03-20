from __future__ import annotations

import datetime
from typing import List, Optional
from enum import Enum
from uuid import uuid4
from sqlalchemy import Column, Enum as SAEnum, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database import Base


class GroupRoleEnum(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


user_group_role_table = Table(
    "user_group_role",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("group_id", ForeignKey("groups.id"), primary_key=True),
    Column("role", SAEnum(GroupRoleEnum), default=GroupRoleEnum.MEMBER),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, default=str(uuid4()))
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    password: Mapped[bytes] = mapped_column(nullable=False)

    group_links: Mapped[List[Group]] = relationship(
        secondary=user_group_role_table, back_populates="user_links"
    )
    owned_groups: Mapped[List[Group]] = relationship(back_populates="owner")

    emitted_invitations: Mapped[List[GroupInvitation]] = relationship(
        foreign_keys="[GroupInvitation.emitter_id]", back_populates="emitter"
    )
    received_invitations: Mapped[List[GroupInvitation]] = relationship(
        foreign_keys="[GroupInvitation.invitee_id]", back_populates="invitee"
    )

    created_expenses: Mapped[List[Expense]] = relationship(back_populates="creator")

    created_subscription_charges: Mapped[List[SubscriptionCharge]] = relationship(
        back_populates="creator"
    )


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(primary_key=True, default=str(uuid4()))

    name: Mapped[str] = mapped_column(nullable=False)
    color: Mapped[Optional[str]]
    icon: Mapped[Optional[str]]

    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    owner: Mapped[User] = relationship(back_populates="owned_groups")

    user_links: Mapped[List[User]] = relationship(
        secondary=user_group_role_table, back_populates="group_links"
    )

    invitations: Mapped[List[GroupInvitation]] = relationship(back_populates="group")

    expenses: Mapped[List[Expense]] = relationship(back_populates="group")


class GroupInvitationStatusEnum(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class GroupInvitation(Base):
    __tablename__ = "group_invitations"

    id: Mapped[str] = mapped_column(primary_key=True, default=str(uuid4()))

    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), index=True)
    group: Mapped[Group] = relationship(back_populates="invitations")

    emitter_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    emitter: Mapped[User] = relationship(
        foreign_keys=[emitter_id], back_populates="emitted_invitations"
    )

    invitee_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    invitee: Mapped[User] = relationship(
        foreign_keys=[invitee_id], back_populates="received_invitations"
    )

    role: Mapped[GroupRoleEnum] = mapped_column(
        nullable=False, default=GroupRoleEnum.MEMBER
    )

    status: Mapped[GroupInvitationStatusEnum] = mapped_column(
        nullable=False, default=GroupInvitationStatusEnum.PENDING
    )


class ExpenseTypeEnum(Enum):
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(primary_key=True, default=str(uuid4()))

    category: Mapped[Optional[str]]
    name: Mapped[str] = mapped_column(nullable=False)
    amount: Mapped[float] = mapped_column(nullable=False)

    creator_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    creator: Mapped[User] = relationship(back_populates="created_expenses")

    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), index=True)
    group: Mapped[Group] = relationship(back_populates="expenses")

    expense_type: Mapped[str]
    __mapper_args__ = {
        "polymorphic_on": "expense_type",
    }


class SubscriptionFrequencyEnum(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class OneTimeExpense(Expense):
    __tablename__ = "one_time_expenses"

    id: Mapped[str] = mapped_column(ForeignKey("expenses.id"), primary_key=True)

    date: Mapped[datetime.date] = mapped_column(nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "one_time",
    }


class Subscription(Expense):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(ForeignKey("expenses.id"), primary_key=True)

    on_every: Mapped[int] = mapped_column(nullable=False, default=1)
    frequency: Mapped[SubscriptionFrequencyEnum] = mapped_column(
        nullable=False, default=SubscriptionFrequencyEnum.MONTHLY
    )

    start_date: Mapped[datetime.date] = mapped_column(nullable=False)
    end_date: Mapped[Optional[datetime.date]] = mapped_column(default=None)

    charges: Mapped[list[SubscriptionCharge]] = relationship(
        back_populates="subscription"
    )

    __mapper_args__ = {
        "polymorphic_identity": "subscription",
    }


class SubscriptionCharge(Base):
    __tablename__ = "subscription_charges"

    id: Mapped[str] = mapped_column(primary_key=True, default=str(uuid4()))

    subscription_id: Mapped[str] = mapped_column(
        ForeignKey("subscriptions.id"), index=True
    )
    subscription: Mapped[Subscription] = relationship(back_populates="charges")
    charged_date: Mapped[datetime.date] = mapped_column(nullable=False)
    amount: Mapped[float] = mapped_column(nullable=False)

    creator_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    creator: Mapped[User] = relationship(back_populates="created_subscription_charges")
