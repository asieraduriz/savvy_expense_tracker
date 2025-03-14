
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Header
from backend.database import get_db
from sqlalchemy.orm import Session

from backend.models.base import Group, Invitation, InvitationStatus, InvitationStatusHistory, OneTimeExpense, SubscriptionExpense, User, UserGroupRole, UserRole
from backend.schemas.create_expense import CreateExpense
from backend.schemas.create_group import CreateGroup
from backend.schemas.create_invitation import CreateInvitation
from backend.schemas.get_group import GroupResponse
from backend.schemas.invitation_response import InvitationResponse
from backend.schemas.update_group import UpdateGroup
from backend.schemas.update_invitation import UpdateInvitation
from backend.security.jwt import get_user_from_auth

router = APIRouter()

@router.post('/group', status_code=201)
def create_group(group: CreateGroup, db: Session = Depends(get_db), authorization: Annotated[str | None, Header()] = None):
    try:
        user_id = get_user_from_auth(authorization)
        
        user = db.query(User).filter(User.id == user_id).one()
        new_group = Group(**group.model_dump(exclude_unset=True), created_by=user)
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
        user_id = get_user_from_auth(authorization)
        user = db.query(User).filter(User.id == user_id).first()
        existing_group = db.query(Group).filter(Group.id == group_id).first()
        if user.id != existing_group.created_by.id: # Need to see if the role is sufficient, not the creator
            raise HTTPException(status_code=403, detail="You are not the creator of this group")

        update_dict = group.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(existing_group, key, value)

        db.commit()
    except Exception as e:
        print('Error updating group', e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Couldn't update group")

@router.get('/groups', response_model=List[GroupResponse])
def get_groups(db: Session = Depends(get_db), authorization: Annotated[str | None, Header()] = None):
    try:
        user_id = get_user_from_auth(authorization)
        groups = db.query(Group).filter(Group.user_group_roles.any(user_id=user_id)).all()
        return groups
    except Exception as e:
        print('Error getting groups', e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Couldn't get groups")
    
@router.get('/group/{group_id}', response_model=GroupResponse)
def get_groups(group_id: str, db: Session = Depends(get_db), authorization: Annotated[str | None, Header()] = None):
    try:
        user_id = get_user_from_auth(authorization)
        group = db.query(Group).filter(Group.id == group_id).first()
        return group
    except Exception as e:
        print('Error getting groups', e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Couldn't get groups")

@router.post('/invitation', status_code=200, response_model=InvitationResponse)
def create_invitation(invitation:CreateInvitation, db: Session = Depends(get_db), authorization: Annotated[str | None, Header()] = None):
    try:
        user_id = get_user_from_auth(authorization)
        user = db.query(User).filter(User.id == user_id).one()
        group = db.query(Group).filter(Group.id == invitation.group_id).one()
        # Need to check for exceptions where the user isn't in the group
        invitee = db.query(User).filter(User.email == invitation.to_user_email).one()

        new_invitation = Invitation(
            inviter=user,
            invitee=invitee,
            group=group,
            role=invitation.role,
            status=InvitationStatus.PENDING
        )

        new_invitation.status_history.append(InvitationStatusHistory(status=InvitationStatus.PENDING, changed_by_user=user))

        db.add(new_invitation)
        db.commit()

        return new_invitation
    except Exception as e:
        print('Error creating invitation', e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Couldn't create invitation")

@router.post('/invitation/{invitation_id}', status_code=200)
def update_invitation(invitation_id: str, invitation: UpdateInvitation, db: Session = Depends(get_db), authorization: Annotated[str | None, Header()] = None):
    try:
        # This call can be requested by two people
        # The inviter can cancel the invitation
        # The invitee can accept or reject the invitation
        # Need to handle both cases
        # And need to handle the case where an invitation is already accepted, cancelled or rejected
        user_id = get_user_from_auth(authorization)
        user = db.query(User).filter(User.id == user_id).one()
        existing_invitation = db.query(Invitation).filter(Invitation.id == invitation_id).one()
        if user.id != existing_invitation.invitee.id:
            raise HTTPException(status_code=403, detail="You are not the invitee of this invitation")

        existing_invitation.status = invitation.status
        existing_invitation.status_history.append(InvitationStatusHistory(status=invitation.status, changed_by_user=user))

        # Need to add user to the group
        existing_invitation.group.user_group_roles.append(UserGroupRole(user=user, group=existing_invitation.group, role=existing_invitation.role))

        db.commit()
    except Exception as e:
        print('Error updating invitation', e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Couldn't update invitation")
    

@router.post('/group/{group_id}/expense', status_code=201)
def create_expense(group_id:str, expense: CreateExpense, db:Session=Depends(get_db), authorization: Annotated[str | None, Header()] = None):
    try:
        user_id = get_user_from_auth(authorization)
        user = db.query(User).filter(User.id == user_id).one()
        group = db.query(Group).filter(Group.id == group_id).one()

        if expense.expense_type == 'one_time_expense':
            one_time_expense = OneTimeExpense(
                group=group,
                creator=user,
                **expense.model_dump(exclude_unset=True)
            )

            db.add(one_time_expense)
            db.commit()

            return one_time_expense
        
        # Maybe request from user if they want to store previous expenses
        # And I need to create subscription entries
        subscription_expense = SubscriptionExpense(
            group=group,
            creator=user,
            **expense.model_dump(exclude_unset=True)
        )
        db.add(subscription_expense)
        db.commit()

        return subscription_expense
    except Exception as e:
        print('Error creating expense', e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Couldn't create expense")