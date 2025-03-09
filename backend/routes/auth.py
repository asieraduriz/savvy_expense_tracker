
import uuid
import bcrypt
from fastapi import APIRouter, Depends
from backend.schemas.user_create import UserCreate
from backend.models.user import User
from backend.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.post('/signup')
def signup_user(user: UserCreate, db: Session=Depends(get_db)):
    db.query(User).filter(User.email == user.email).first()

    new_user = User(id=str(uuid.uuid4()), name=user.name, email=user.email, password=bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    pass