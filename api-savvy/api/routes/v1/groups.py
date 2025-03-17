import enum
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status

from pydantic import BaseModel
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import (
    Group,
    GroupInvitation,
    GroupInvitationStatusEnum,
    GroupRoleEnum,
    User,
    user_group_role_table,
)
from api.security import get_user_from_auth

from api.src.find_first import find_first

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
    authorization: Annotated[str | None, Header()] = None,
):
    user = get_user_from_auth(authorization, db)

    try:
        new_group = Group(
            id=str(uuid4()),
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


class InviteCreate(BaseModel):
    invitee_id: str
    role: Optional[GroupRoleEnum] = GroupRoleEnum.MEMBER


class InvitationResponse(BaseModel):
    id: str
    group_id: str
    role: GroupRoleEnum
    status: GroupInvitationStatusEnum


@router.post("/groups/{group_id}/invite/", status_code=status.HTTP_201_CREATED)
def invite_to_group(
    group_id: str,
    invitation: InviteCreate,
    db: Session = Depends(get_db),
    authorization: Annotated[str | None, Header()] = None,
):
    user = get_user_from_auth(authorization, db)
    if user.id == invitation.invitee_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    query = select(user_group_role_table).where(
        user_group_role_table.c.user_id == user.id,
        user_group_role_table.c.group_id == group_id,
    )
    result = db.execute(query).first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User not in group"
        )

    invitee_user = db.query(User).filter(User.id == invitation.invitee_id).first()
    if invitee_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitee not found"
        )

    if result[2] not in [GroupRoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough privileges to invite",
        )

    try:
        db_invitation = GroupInvitation(
            group_id=group_id,
            emitter_id=user.id,
            invitee_id=invitation.invitee_id,
            role=invitation.role,
        )

        db.add(db_invitation)
        db.commit()

        return InvitationResponse(
            id=db_invitation.id,
            group_id=db_invitation.group_id,
            role=db_invitation.role,
            status=db_invitation.status,
        )
    except Exception as e:
        db.rollback()
        print("Exception e", e)


class InviteeRsvpEnum(str, enum.Enum):
    ACCEPTED = GroupInvitationStatusEnum.ACCEPTED.value
    REJECTED = GroupInvitationStatusEnum.REJECTED.value


class InvitationRsvp(BaseModel):
    rsvp: InviteeRsvpEnum


@router.post("/groups/invitations/{invitation_id}/rsvp")
def rsvp_invitation(
    invitation_id: str,
    invitation_rsvp: InvitationRsvp,
    db: Session = Depends(get_db),
    authorization: Annotated[str | None, Header()] = None,
):
    user = get_user_from_auth(authorization, db)

    invitation = (
        db.query(GroupInvitation)
        .filter(GroupInvitation.id == invitation_id)
        .filter(GroupInvitation.invitee_id == user.id)
        .first()
    )

    if invitation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
        )

    if invitation.status != GroupInvitationStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Invitation already rsvp'd"
        )

    invitation.status = invitation_rsvp.rsvp

    if invitation_rsvp.rsvp == GroupInvitationStatusEnum.ACCEPTED:
        db.execute(
            user_group_role_table.insert().values(
                user_id=user.id, group_id=invitation.group_id, role=invitation.role
            )
        )

    db.commit()

    return InvitationResponse(
        id=invitation.id,
        group_id=invitation.group_id,
        role=invitation.role,
        status=invitation.status,
    )


@router.delete("/groups/invitations/{invitation_id}")
def withdraw_invitation(
    invitation_id: str,
    db: Session = Depends(get_db),
    authorization: Annotated[str | None, Header()] = None,
):
    user = get_user_from_auth(authorization, db)

    invitation = (
        db.query(GroupInvitation)
        .filter(GroupInvitation.id == invitation_id)
        .filter(GroupInvitation.emitter_id == user.id)
        .first()
    )

    if invitation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
        )

    if invitation.status != GroupInvitationStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Invitation already rsvp'd"
        )

    invitation.status = GroupInvitationStatusEnum.WITHDRAWN

    db.commit()

    return InvitationResponse(
        id=invitation.id,
        group_id=invitation.group_id,
        role=invitation.role,
        status=invitation.status,
    )
