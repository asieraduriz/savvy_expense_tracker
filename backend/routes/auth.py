
import bcrypt
from fastapi import APIRouter, Depends
from backend.schemas.user_create import UserCreate
from backend.database import get_db
from sqlalchemy.orm import Session

from backend.models.base import User

import uuid

router = APIRouter()

@router.post('/signup')
def signup_user(user: UserCreate, db: Session=Depends(get_db)):
    db.query(User).filter(User.email == user.email).first()

    new_user = User(name=user.name, email=user.email, password=bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()), username=user.username)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # # Step 1: Create a User

    # category_name = 'Supermarket'
    # group_name = 'La vida'
    
    # # Create two users
    # user_1 = User(username="user1", name="User One", email="user1@example.com", password=b"password")
    # user_2 = User(username="user2", name="User Two", email="user2@example.com", password=b"password")
    # db.add(user_1)
    # db.add(user_2)
    # db.commit()

    # # Create a group named "Groceries"
    # group = Group(name="Groceries")
    # db.add(group)
    # db.commit()

    # # Assign roles to users in the group
    # user_group_role_1 = UserGroupRole(user_id=user_1.id, group_id=group.id, role=UserRole.ADMIN)
    # db.add(user_group_role_1)
    # db.commit()

    # # Send an invitation from user_1 to user_2 to join the "Groceries" group, and specify the role
    # invitation = Invitation(
    #     inviter=user_1,
    #     invitee=user_2,
    #     group=group,
    #     status=InvitationStatus.PENDING,
    #     role=UserRole.MEMBER  # Track role in the invitation
    # )
    # db.add(invitation)
    # db.commit()

    # # Log the invitation status change
    # status_history = InvitationStatusHistory(
    #     invitation_id=invitation.id,
    #     status=InvitationStatus.PENDING,
    #     changed_at=datetime.now(timezone.utc),
    #     changed_by_user_id=user_1.id
    # )
    # db.add(status_history)
    # db.commit()

    # # User_2 accepts the invitation
    # invitation.status = InvitationStatus.ACCEPTED
    # db.commit()

    # # Log the status change (user_2 accepts the invitation)
    # status_history = InvitationStatusHistory(
    #     invitation_id=invitation.id,
    #     status=InvitationStatus.ACCEPTED,
    #     changed_at=datetime.now(timezone.utc),
    #     changed_by_user_id=user_2.id
    # )
    # db.add(status_history)
    # db.commit()

    # # After acceptance, user_2 gets assigned the role as specified in the invitation
    # user_group_role_2 = UserGroupRole(user_id=user_2.id, group_id=group.id, role=invitation.role)
    # db.add(user_group_role_2)
    # db.commit()

    # # User_2 creates an OneTimeExpense and SubscriptionExpense with category "Supermarket"
    # category = ExpenseCategory(name="Supermarket", icon="supermarket-icon")
    # db.add(category)
    # db.commit()

    # one_time_expense = OneTimeExpense(
    #     group_id=group.id,
    #     creator_id=user_2.id,
    #     category_id=category.id,
    #     expense_type="one_time_expense"
    # )
    # db.add(one_time_expense)

    # subscription_expense = SubscriptionExpense(
    #     group_id=group.id,
    #     creator_id=user_2.id,
    #     category_id=category.id,
    #     expense_type="subscription_expense"
    # )
    # db.add(subscription_expense)
    
    # db.commit()

    # # Print invitation status history for review
    # for history in invitation.status_history:
    #     print(f"Status: {history.status}, Changed By: {history.changed_by_user.username}, At: {history.changed_at}")


@router.get('/main')
def get_main(db: Session=Depends(get_db)):
    user =db.query(User).filter(User.username == 'aaduriz').first()
    user_string = f"User(id={user.id}, username={user.username}, name={user.name}, email={user.email}, groups=["

    # Stringify Groups
    group_strings = [f"Group(id={group.id})" for group in user.groups]
    user_string += ", ".join(group_strings) + "])"

    return user_string
