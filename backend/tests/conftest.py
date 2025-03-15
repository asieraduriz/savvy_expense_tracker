import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from backend.main import app
from backend.database import get_db
from backend.models.base import Base

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

@pytest.fixture(scope="session")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def session(test_db):
    session = TestingSessionLocal()
    yield session
    session.rollback()
    TestingSessionLocal.remove()

@pytest.fixture()
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]