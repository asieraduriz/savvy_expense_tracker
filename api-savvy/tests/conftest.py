# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session
from api.database import Base, get_db
from api.main import app

@pytest.fixture(name="test_db")
def session_fixture():
    engine = create_engine(
        "sqlite:///memory.db", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        Base.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(test_db: Session):
    def get_session_override():
        return test_db

    app.dependency_overrides[get_db] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
