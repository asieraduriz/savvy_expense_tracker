
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Header
from backend.database import get_db
from sqlalchemy.orm import Session

from backend.models.base import Group, User, UserGroupRole, UserRole
from backend.schemas.create_group import CreateGroup
from backend.security.jwt import decode_jwt

router = APIRouter()

@router.put('/group', status_code=201)
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
    except Exception as e:
        print('Error creating group', e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Couldn't create group")
