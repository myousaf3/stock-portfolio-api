import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import get_db, Base

# Import app from main module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app as fastapi_app

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


@pytest.mark.asyncio
async def test_health_check(setup_database):
    """Test health check endpoint"""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        response = await ac.get("/healthz")
    
    assert response.status_code == 200
    data = response.json()
    assert "ok" in data
    assert data["ok"] is True


@pytest.mark.asyncio
async def test_health_check_database_status(setup_database):
    """Test health check includes database status"""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        response = await ac.get("/healthz")
    
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert data["database"] == "connected"