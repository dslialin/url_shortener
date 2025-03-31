import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Adjust the import path according to your project structure
from app.main import app
from app.database import Base, get_db
# Added for user fixture
import app.models as models
from app.auth import get_password_hash

# Use SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Needed only for SQLite
    poolclass=StaticPool, # Use StaticPool for in-memory SQLite
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fixture to override the get_db dependency
@pytest.fixture(scope="function")
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Fixture to set up the database for each test function
@pytest.fixture(scope="function", autouse=True)
def setup_database(override_get_db):
    # Create the tables
    Base.metadata.create_all(bind=engine)
    # Run the test function (yield)
    yield
    # Drop the tables after the test is done
    Base.metadata.drop_all(bind=engine)

# Fixture to provide a simple test user dictionary
@pytest.fixture(scope="session")
def test_user_data():
    return {
        "username": "testuser_fixture",
        "email": "test_fixture@example.com",
        "password": "fixture_password"
    }

# Fixture to create a user in the database
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

# Fixture to provide a TestClient instance (unauthenticated)
@pytest.fixture(scope="function")
def client(override_get_db):
    # Apply the dependency override for this client instance
    app.dependency_overrides[get_db] = lambda: override_get_db
    with TestClient(app) as test_client:
        yield test_client
    # Clean up the override after the test using this client
    app.dependency_overrides.clear()

# Fixture to provide an authenticated TestClient instance
@pytest.fixture(scope="function")
def auth_client(override_get_db, test_user_data, db_user):
    # Apply the dependency override for this client instance
    app.dependency_overrides[get_db] = lambda: override_get_db

    # Create a new client instance specifically for authentication
    with TestClient(app) as authenticated_test_client:
        # Need db_user fixture to ensure user exists before login
        response = authenticated_test_client.post(
            "/token",
            data={"username": test_user_data["username"], "password": test_user_data["password"]}
        )
        assert response.status_code == 200 # Make sure login is successful
        token = response.json()["access_token"]
        # Set headers for this specific authenticated client
        authenticated_test_client.headers = {"Authorization": f"Bearer {token}"}
        yield authenticated_test_client # Yield the authenticated client
    
    # Clean up the override after the test using this client
    app.dependency_overrides.clear() 