from fastapi import APIRouter, Depends

from pydantic import BaseModel

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
            name=group.name,
            color=group.color,
            icon=group.icon,
            owner=user,
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
            owner_id=new_group.owner.id,
            owner_name=new_group.owner.name,
        )
    except Exception as e:
        db.rollback()
        print("Exception e", e)
