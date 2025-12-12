import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import get_db, Base
from app.services.auth import AuthService

# Import app from main module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app as fastapi_app

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://portfolio:portfolio@localhost:5432/portfolio_test"

engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def setup_database():
    """Create test database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_user():
    """Create a test user"""
    async with TestSessionLocal() as db:
        auth_service = AuthService(db)
        user = await auth_service.create_user(
            email="test@example.com",
            password="testpassword123",
            full_name="Test User"
        )
        return user


@pytest.mark.asyncio
async def test_login_success(setup_database, test_user):
    """Test successful login"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(setup_database, test_user):
    """Test login with invalid password"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"}
        )
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(setup_database):
    """Test login with non-existent user"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "password"}
        )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_social_auth_google(setup_database):
    """Test Google social authentication"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/social?provider=google",
            json={"token": "mock-google-token"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["provider"] == "google"


@pytest.mark.asyncio
async def test_social_auth_facebook(setup_database):
    """Test Facebook social authentication"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/social?provider=facebook",
            json={"token": "mock-facebook-token"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["provider"] == "facebook"


@pytest.mark.asyncio
async def test_social_auth_invalid_provider(setup_database):
    """Test social auth with invalid provider"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/auth/social?provider=twitter",
            json={"token": "mock-token"}
        )
    
    assert response.status_code == 400
    assert "Invalid provider" in response.json()["detail"]


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(setup_database):
    """Test accessing protected endpoint without token"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/portfolio")
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_protected_endpoint_with_token(setup_database, test_user):
    """Test accessing protected endpoint with valid token"""
    # Login first to get token
    async with AsyncClient(app=app, base_url="http://test") as ac:
        login_response = await ac.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"}
        )
        token = login_response.json()["access_token"]
        
        # Access protected endpoint
        response = await ac.get(
            "/portfolio",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200