import enum
from typing import List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status

from pydantic import BaseModel

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import get_db
from api.iterable_operations import find_first
from api.models import (
    GroupInvitation,
    GroupInvitationStatusEnum,
    GroupRoleEnum,
    User,
    user_group_role_table,
)
from api.middlewares import get_authenticated_user


router = APIRouter()


class InvitationCreate(BaseModel):
    invitee_email: str
    role: Optional[GroupRoleEnum] = GroupRoleEnum.MEMBER


class InvitationResponse(BaseModel):
    id: str
    group_id: str
    group_name: str
    role: GroupRoleEnum
    status: GroupInvitationStatusEnum


@router.post("/groups/{group_id}/invite/", status_code=status.HTTP_201_CREATED)
def create_invitation(
    group_id: str,
    invitation: InvitationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_authenticated_user),
):
    if user.email == invitation.invitee_email:
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

    invitee_user = db.query(User).filter(User.email == invitation.invitee_email).first()
    if invitee_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitee not found"
        )

    if result[2] not in [GroupRoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough privileges to invite",
        )

    existing_invitation = find_first(
        invitee_user.received_invitations,
        lambda invitation: invitation.group_id == group_id,
    )
    if (
        existing_invitation is not None
        and existing_invitation.status == GroupInvitationStatusEnum.PENDING
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invitee already has a pending invitation",
        )

    if find_first(
        invitee_user.group_links, lambda group_link: group_link.id == group_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Invitee already in group"
        )

    try:
        db_invitation = GroupInvitation(
            id=str(uuid4()),
            group_id=group_id,
            emitter_id=user.id,
            invitee_id=invitee_user.id,
            role=invitation.role,
        )

        db.add(db_invitation)
        db.commit()

        return _process_invitation(db_invitation)
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
    user: User = Depends(get_authenticated_user),
):

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

    return _process_invitation(invitation)


@router.delete("/groups/invitations/{invitation_id}")
def withdraw_invitation(
    invitation_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_authenticated_user),
):

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

    return _process_invitation(invitation)


def _process_invitations(
    invitations: List[GroupInvitation],
) -> List[InvitationResponse]:
    """Helper function to process a list of invitations."""
    return [_process_invitation(invitation) for invitation in invitations]


def _process_invitation(invitation: GroupInvitation):
    """Helper function to process a list of invitations."""
    return InvitationResponse(
        id=invitation.id,
        group_id=invitation.group_id,
        group_name=invitation.group.name,
        role=invitation.role,
        status=invitation.status,
    )


@router.get("/groups/invitations/", response_model=list[InvitationResponse])
def get_invitations(user: User = Depends(get_authenticated_user)):
    return _process_invitations([*user.emitted_invitations, *user.received_invitations])


@router.get("/groups/invitations/received", response_model=list[InvitationResponse])
def get_received_invitations(user: User = Depends(get_authenticated_user)):
    return _process_invitations(user.received_invitations)


@router.get("/groups/invitations/emitted", response_model=list[InvitationResponse])
def get_invitations(user: User = Depends(get_authenticated_user)):
    return _process_invitations(user.emitted_invitations)
