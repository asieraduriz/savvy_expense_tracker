from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends

from pydantic import BaseModel

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import (
    Group,
    GroupRoleEnum,
    User,
    user_group_role_table,
)

from api.middlewares import get_authenticated_user


router = APIRouter()


class GroupCreate(BaseModel):
    name: str
    color: str | None = None
    icon: str | None = None


class GroupResponse(BaseModel):
    id: str
    name: str
    color: str | None
    icon: str | None
    owner_id: str
    owner_name: str


@router.post("/groups/", status_code=201, response_model=GroupResponse)
def create_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_authenticated_user),
):
    try:
        new_group = Group(
            id=str(uuid4()),
            name=group.name,
            color=group.color,
            icon=group.icon,
            owner=user,
        )
        db.add(new_group)
        db.commit()

        db.execute(
            user_group_role_table.insert().values(
                user_id=user.id, group_id=new_group.id, role=GroupRoleEnum.ADMIN
            )
        )

        db.commit()

        return GroupResponse(
            id=new_group.id,
            name=new_group.name,
            color=new_group.color,
            icon=new_group.icon,
            owner_id=new_group.owner.id,
            owner_name=new_group.owner.name,
        )
    except Exception as e:
        db.rollback()
        print("Exception e", e)


@router.get("/groups/", response_model=List[GroupResponse])
def get_groups(
    db: Session = Depends(get_db), user: User = Depends(get_authenticated_user)
):
    user_group_links = db.query(User).filter(User.id == user.id).first().group_links
    stmt = (
        select(user_group_role_table)
        .where(user_group_role_table.c.user_id == user.id)
        .join(Group)
    )

    result = db.execute(stmt).all()

    group_response: List[GroupResponse] = []
    for group in user_group_links:
        group_dict = GroupResponse(
            id=group.id,
            name=group.name,
            color=group.color,
            icon=group.icon,
            owner_id=group.owner_id,
            owner_name=group.owner.name,
        )
        group_response.append(group_dict)

    return group_response
