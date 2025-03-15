from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.base import User


def test_create_user(client: TestClient, session: Session):
    user_data = {"name": "newuser", "email": "newuser@example.com", "password": "password"}
    response = client.post("/auth/signup/", json=user_data)
    assert response.status_code == 200
    user = session.query(User).filter(User.name == "newuser").first()
    assert user is not None

def test_duplicate_user(client: TestClient, session: Session):
    existing_user = User(name="duplicate", email="duplicate@example.com", password=b"hashed")
    session.add(existing_user)
    session.commit()
    user_data = {"name": "duplicate", "email": "newemail@example.com", "password":"password"}
    response = client.post("/auth/signup/", json=user_data)
    assert response.status_code == 400

# Add more user-related tests here