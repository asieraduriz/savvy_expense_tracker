from __future__ import annotations

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
    Column("role", SAEnum(GroupRoleEnum)),
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


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    color: Mapped[Optional[str]]
    icon: Mapped[Optional[str]]

    user_links: Mapped[List[User]] = relationship(
        secondary=user_group_role_table, back_populates="group_links"
    )
