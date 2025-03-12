from __future__ import annotations
import uuid, enum, datetime
from typing import List

from sqlalchemy import LargeBinary, DateTime, ForeignKey, Enum, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.mixins import TimestampMixin

Base = declarative_base()

# Define an Enum for roles
class UserRole(enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class InvitationStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class Invitation(Base, TimestampMixin):
    __tablename__ = 'invitation'

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    inviter_id: Mapped[str] = mapped_column(ForeignKey("user.id"), nullable=False)
    invitee_id: Mapped[str] = mapped_column(ForeignKey("user.id"), nullable=False)
    group_id: Mapped[str] = mapped_column(ForeignKey("group.id"), nullable=False)
    status: Mapped[InvitationStatus] = mapped_column(Enum(InvitationStatus), nullable=False, default=InvitationStatus.PENDING)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)  # Track the role in the invitation
    
    inviter: Mapped[User] = relationship("User", foreign_keys=[inviter_id])
    invitee: Mapped[User] = relationship("User", foreign_keys=[invitee_id])
    group: Mapped[Group] = relationship("Group")

    # Relationship to status history (cascades on delete, orphan removal)
    status_history: Mapped[List[InvitationStatusHistory]] = relationship("InvitationStatusHistory", back_populates="invitation", cascade="all, delete-orphan")


class InvitationStatusHistory(Base):
    __tablename__ = 'invitation_status_history'

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    invitation_id: Mapped[str] = mapped_column(ForeignKey("invitation.id"), nullable=False)
    status: Mapped[InvitationStatus] = mapped_column(Enum(InvitationStatus), nullable=False)
    changed_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship to Invitation and the User who made the change
    invitation: Mapped[Invitation] = relationship("Invitation", back_populates="status_history")
    changed_by_user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), nullable=False)
    changed_by_user: Mapped[User] = relationship("User")


# Many-to-Many relationship between Users, Groups, and Roles
class UserGroupRole(Base):
    __tablename__ = "user_group_role"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), nullable=False)
    group_id: Mapped[str] = mapped_column(ForeignKey("group.id"), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)

    # Relationships
    user: Mapped[User] = relationship(back_populates="user_group_roles")
    group: Mapped[Group] = relationship(back_populates="user_group_roles")


class User(Base, TimestampMixin):
    __tablename__ = 'user'

    id: Mapped[str] = mapped_column(primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    password: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)

    # Users are linked to groups through UserGroupRole
    user_group_roles: Mapped[List[UserGroupRole]] = relationship(back_populates="user")
    # Sent and received invitations
    sent_invitations: Mapped[List[Invitation]] = relationship("Invitation", foreign_keys=[Invitation.inviter_id], back_populates="inviter")
    received_invitations: Mapped[List[Invitation]] = relationship("Invitation", foreign_keys=[Invitation.invitee_id], back_populates="invitee")

class Group(Base, TimestampMixin):
    __tablename__ = 'group'

    id: Mapped[str] = mapped_column(primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(nullable=False, index=True)

    created_by_id: Mapped[str] = mapped_column(ForeignKey("user.id"), nullable=False)
    created_by: Mapped[User] = relationship("User")

    # Groups are linked to users through UserGroupRole
    user_group_roles: Mapped[List[UserGroupRole]] = relationship(back_populates="group")
    # Invitations for the group
    invitations: Mapped[List[Invitation]] = relationship("Invitation", back_populates="group")

    expenses: Mapped[List[Expense]] = relationship(back_populates='group')


class Expense(Base, TimestampMixin):
    __tablename__ = 'expense'

    id: Mapped[str] = mapped_column(primary_key=True, index=True, default=lambda: str(uuid.uuid4()))

    group_id: Mapped[str] = mapped_column(ForeignKey("group.id"))
    group: Mapped[Group] = relationship(back_populates="expenses")

    creator_id: Mapped[str] = mapped_column(ForeignKey("user.id"))
    creator: Mapped[User] = relationship()

    category_id: Mapped[str] = mapped_column(ForeignKey("expense_category.id"))
    category: Mapped[ExpenseCategory] = relationship(back_populates='expenses')

    expense_type: Mapped[str]

    __mapper_args__ = {
        "polymorphic_identity": "expense",
        "polymorphic_on": "expense_type",
    }


class OneTimeExpense(Expense):
    __tablename__ = 'one_time_expense'

    id: Mapped[str] = mapped_column(ForeignKey("expense.id"), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'one_time_expense',
    }


class SubscriptionExpense(Expense):
    __tablename__ = 'subscription_expense'

    id: Mapped[str] = mapped_column(ForeignKey("expense.id"), primary_key=True)

    cadence_days: Mapped[int] = mapped_column(nullable=False, default=30)
    __mapper_args__ = {
        'polymorphic_identity': 'subscription_expense',
    }


class ExpenseCategory(Base, TimestampMixin):
    __tablename__ = 'expense_category'

    id: Mapped[str] = mapped_column(primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(nullable=False, index=True)
    icon: Mapped[str] = mapped_column(nullable=True)

    expenses: Mapped[List[Expense]] = relationship(back_populates='category')

