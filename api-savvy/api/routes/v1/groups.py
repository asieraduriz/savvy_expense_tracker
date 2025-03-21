from typing import List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Response

from pydantic import BaseModel

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import get_db
from api.iterable_operations import find_first, object_is_empty
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


class GroupPatch(BaseModel):
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None


class GroupPatchResponse(GroupPatch):
    id: str


@router.patch(
    "/groups/{group_id}",
    response_model=GroupPatchResponse | None,
    status_code=status.HTTP_200_OK,
)
def patch_group(
    group_id: str,
    group: GroupPatch,
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_authenticated_user),
):
    if object_is_empty(group.model_dump(exclude_unset=True)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    db_group = find_first(
        user.group_links, lambda group_link: group_link.id == group_id
    )

    if db_group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )

    stmt = select(user_group_role_table).where(
        user_group_role_table.c.user_id == user.id,
        user_group_role_table.c.group_id == group_id,
    )

    result = db.execute(stmt).first()
    if result[2] not in [GroupRoleEnum.ADMIN, GroupRoleEnum.MEMBER]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Insufficient privileges",
        )

    group_fields_for_patch_data = {
        key: getattr(db_group, key) for key in group.model_fields
    }

    if group_fields_for_patch_data == group.model_dump():
        response.status_code = status.HTTP_204_NO_CONTENT
        return

    db_group.name = group.name
    db_group.color = group.color
    db_group.icon = group.icon

    db.commit()

    patch_response = GroupPatchResponse(**group.model_dump(), id=group_id)
    print("response", patch_response)
    return patch_response
