

from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from api.database import get_session
from api.models import User
from api.security import create_access_token, hash_password, verify_password

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()

class UserSignup(BaseModel):
    name: str
    email: str
    password: str

class UserSignupResponse(BaseModel):
    id: int
    name: str
    email: str
    access_token: str

@router.post("/signup/", status_code=201, response_model=UserSignupResponse)
def signup(*, session: Session = Depends(get_session), user: UserSignup):
    try:
        db_user = User(name=user.name, email=user.email, password=hash_password(user.password))
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return UserSignupResponse(**db_user.model_dump(exclude={'password'}), access_token=create_access_token(db_user.id))
    except IntegrityError as e:
        if 'user.email' in e._message():
            raise HTTPException(status_code=409, detail={'duplicates': ['email']})
        raise HTTPException(status_code=500, detail=f'Error creating user {e}')
    

class UserLogin(BaseModel):
    email: str
    password: str

class UserLoginResponse(BaseModel):
    id: int
    name: str
    email: str
    access_token: str


@router.post("/login/", response_model=UserLoginResponse)
def login(*, session: Session = Depends(get_session), user: UserLogin):
    query = select(User).where(User.email == user.email)
    results = session.exec(query)
    db_user = results.first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail='Incorrect email or password')
    return UserLoginResponse(**db_user.model_dump(exclude={'password'}), access_token=create_access_token(db_user.id))