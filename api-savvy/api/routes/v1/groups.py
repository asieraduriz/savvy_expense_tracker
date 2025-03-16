from typing import Annotated
from fastapi import APIRouter, Depends, Header

from pydantic import BaseModel
from uuid import uuid4

from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Group, GroupRoleEnum, user_group_role_table
from api.security import get_user_from_auth

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


@router.post("/groups/", status_code=201, response_model=GroupResponse)
def create_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    authorization: Annotated[str | None, Header()] = None,
):
    print("Authorizaton", authorization)
    user = get_user_from_auth(authorization, db)

    try:
        new_group = Group(
            id=str(uuid4()),
            name=group.name,
            color=group.color,
            icon=group.icon,
        )
        db.add(new_group)
        db.flush()

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
        )
    except Exception as e:
        db.rollback()
        print("Exception e", e)
