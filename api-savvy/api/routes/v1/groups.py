

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Header

from pydantic import BaseModel
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from uuid import uuid4

from api.database import get_session
from api.models import Group, GroupRoleEnum, User, UserGroupLink
from api.security import create_access_token, get_user_from_auth, hash_password, verify_password

router = APIRouter()

class GroupCreate(BaseModel):
    name: str
    color: str
    icon: str


@router.post("/groups/", status_code=201)
def create_group(*, session: Session = Depends(get_session), group: GroupCreate, authorization: Annotated[str | None, Header()] = None):
    print("Authorizaton", authorization)
    user = get_user_from_auth(authorization, session)

    try:
        new_group = Group(
            id=str(uuid4()),
            name=group.name,
            color=group.color,
            icon=group.icon,
            owner=user
        )

        new_link = UserGroupLink(
            user_id=user.id,
            group_id=new_group.id,
            role=GroupRoleEnum.ADMIN
        )

        session.add(new_group)
        session.add(new_link)

        session.commit()

        return new_group

    except Exception as e:
        session.rollback()