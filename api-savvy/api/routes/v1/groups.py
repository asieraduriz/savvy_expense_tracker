

from typing import Annotated
from fastapi import APIRouter, Depends, Header

from pydantic import BaseModel
from uuid import uuid4

from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Group, GroupRoleEnum
from api.security import get_user_from_auth

router = APIRouter()

class GroupCreate(BaseModel):
    name: str
    color: str
    icon: str


@router.post("/groups/", status_code=201)
def create_group(*, db: Session = Depends(get_db), group: GroupCreate, authorization: Annotated[str | None, Header()] = None):
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

        db.commit()

        return new_group

    except Exception as e:
        db.rollback()