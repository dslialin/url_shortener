import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
import app.models as models
from app.auth import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function", autouse=True)
def setup_database(override_get_db):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def test_user_data():
    return {
        "username": "testuser_fixture",
        "email": "test_fixture@example.com",
        "password": "fixture_password"
    }

@pytest.fixture(scope="function")
def db_user(override_get_db, test_user_data):
    db = override_get_db
    hashed_password = get_password_hash(test_user_data["password"])
    user = models.User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def client(override_get_db):
    app.dependency_overrides[get_db] = lambda: override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def auth_client(override_get_db, test_user_data, db_user):
    app.dependency_overrides[get_db] = lambda: override_get_db

    with TestClient(app) as authenticated_test_client:
        response = authenticated_test_client.post(
            "/token",
            data={"username": test_user_data["username"], "password": test_user_data["password"]}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        authenticated_test_client.headers = {"Authorization": f"Bearer {token}"}
        yield authenticated_test_client
    
    app.dependency_overrides.clear() 