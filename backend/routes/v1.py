
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Header
from backend.database import get_db
from sqlalchemy.orm import Session

from backend.models.base import Group, User, UserGroupRole, UserRole
from backend.schemas.create_group import CreateGroup
from backend.schemas.update_group import UpdateGroup
from backend.security.jwt import decode_jwt

router = APIRouter()

@router.post('/group', status_code=201)
def create_group(group: CreateGroup, db: Session = Depends(get_db), authorization: Annotated[str | None, Header()] = None):
    try:
        payload = decode_jwt(authorization)
        if not payload:
            return HTTPException({"message": "Invalid token"}, status_code=401)
        
        user_id = payload.sub
        user = db.query(User).filter(User.id == user_id).one()
        new_group = Group(name=group.name, created_by=user)
        user_group_role = UserGroupRole(role=UserRole.ADMIN, user=user, group=new_group)

        db.add(user_group_role)

        db.commit()

        return {"group_id": new_group.id}
    except Exception as e:
        print('Error creating group', e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Couldn't create group")

@router.patch('/group/{group_id}', status_code=200)
def update_group(group_id: str, group: UpdateGroup, db: Session = Depends(get_db), authorization: Annotated[str | None, Header()] = None):
    try:
        payload = decode_jwt(authorization)
        if not payload:
            return HTTPException({"message": "Invalid token"}, status_code=401)
        
        user_id = payload.sub
        user = db.query(User).filter(User.id == user_id).first()
        existing_group = db.query(Group).filter(Group.id == group_id).first()
        print("Existing group", existing_group.__dict__)
        if user.id != existing_group.created_by.id:
            raise HTTPException(status_code=403, detail="You are not the creator of this group")

        update_dict = group.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(existing_group, key, value)

        print('Updated group', existing_group.__dict__)
        db.commit()
    except Exception as e:
        print('Error updating group', e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Couldn't update group")