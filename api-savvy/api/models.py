from typing import List, Optional
import sqlalchemy
from sqlmodel import Enum, Field, Relationship, SQLModel
from sqlalchemy import Column, Enum as SAEnum

class GroupRoleEnum(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"
    
class UserGroupLink(SQLModel, table=True):
    user_id: Optional[str] = Field(default=None, foreign_key="user.id", primary_key=True)
    user: "User" = Relationship(back_populates="group_links")

    group_id: Optional[str] = Field(default=None, foreign_key="group.id", primary_key=True)
    group: "Group" = Relationship()

    role: GroupRoleEnum = Field(sa_column=Column(SAEnum(GroupRoleEnum)))  # Mapping Enum to SQL


class User(SQLModel, table=True):
    id: Optional[str] = Field(index=True, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    password: bytes
    group_links: list[UserGroupLink]= Relationship(back_populates="user")


class Group(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    color: Optional[str] = Field(nullable=True)
    icon: Optional[str] = Field(nullable=True)

    owner_id: str = Field(foreign_key="user.id")

    user_links: list[User] = Relationship(back_populates="group")



