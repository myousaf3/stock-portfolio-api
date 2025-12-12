import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from datetime import datetime

from app.core.database import get_db, Base
from app.services.auth import AuthService
from app.models.models import Ticker, Price

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


@pytest.fixture
async def test_user_with_token():
    """Create a test user and return auth token"""
    async with TestSessionLocal() as db:
        auth_service = AuthService(db)
        user = await auth_service.create_user(
            email="portfolio@example.com",
            password="testpassword123",
            full_name="Portfolio Test User"
        )
        token = auth_service.create_access_token(user.id, user.email)
        return user, token


@pytest.fixture
async def sample_tickers():
    """Create sample tickers with price data"""
    async with TestSessionLocal() as db:
        # Create tickers
        aapl = Ticker(symbol="AAPL", name="Apple Inc.", sector="Technology")
        googl = Ticker(symbol="GOOGL", name="Alphabet Inc.", sector="Technology")
        
        db.add(aapl)
        db.add(googl)
        await db.commit()
        await db.refresh(aapl)
        await db.refresh(googl)
        
        # Add price data
        prices = [
            Price(ticker_id=aapl.id, date=datetime(2024, 1, 1), close_price=180.0, 
                  open_price=178.0, high_price=182.0, low_price=177.0, volume=1000000),
            Price(ticker_id=aapl.id, date=datetime(2024, 1, 2), close_price=182.0,
                  open_price=180.0, high_price=184.0, low_price=179.0, volume=1100000),
            Price(ticker_id=googl.id, date=datetime(2024, 1, 1), close_price=140.0,
                  open_price=138.0, high_price=142.0, low_price=137.0, volume=800000),
            Price(ticker_id=googl.id, date=datetime(2024, 1, 2), close_price=138.0,
                  open_price=140.0, high_price=141.0, low_price=137.0, volume=850000),
        ]
        
        for price in prices:
            db.add(price)
        
        await db.commit()
        return [aapl, googl]


@pytest.mark.asyncio
async def test_get_portfolio_structure(setup_database, test_user_with_token, sample_tickers):
    """Test portfolio endpoint returns correct structure"""
    user, token = test_user_with_token
    
    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        response = await ac.get(
            "/portfolio",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "holdings" in data
    assert "totalValue" in data
    assert isinstance(data["holdings"], list)
    assert isinstance(data["totalValue"], (int, float))


@pytest.mark.asyncio
async def test_portfolio_holdings_format(setup_database, test_user_with_token, sample_tickers):
    """Test each holding has required fields"""
    user, token = test_user_with_token
    
    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        response = await ac.get(
            "/portfolio",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    data = response.json()
    
    if len(data["holdings"]) > 0:
        holding = data["holdings"][0]
        assert "ticker" in holding
        assert "name" in holding
        assert "qty" in holding
        assert "price" in holding
        assert "dailyChangePct" in holding
        assert "value" in holding
        
        # Check types
        assert isinstance(holding["ticker"], str)
        assert isinstance(holding["name"], str)
        assert isinstance(holding["qty"], int)
        assert isinstance(holding["price"], (int, float))
        assert isinstance(holding["dailyChangePct"], (int, float))
        assert isinstance(holding["value"], (int, float))


@pytest.mark.asyncio
async def test_portfolio_total_value_calculation(setup_database, test_user_with_token, sample_tickers):
    """Test that total value equals sum of holding values"""
    user, token = test_user_with_token
    
    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        response = await ac.get(
            "/portfolio",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    data = response.json()
    
    calculated_total = sum(h["value"] for h in data["holdings"])
    assert abs(data["totalValue"] - calculated_total) < 0.01  # Allow for rounding


@pytest.mark.asyncio
async def test_portfolio_consistency(setup_database, test_user_with_token, sample_tickers):
    """Test that same user gets same portfolio across requests"""
    user, token = test_user_with_token
    
    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        # First request
        response1 = await ac.get(
            "/portfolio",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Second request
        response2 = await ac.get(
            "/portfolio",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Same number of holdings
    assert len(data1["holdings"]) == len(data2["holdings"])
    
    # Same tickers and quantities
    tickers1 = {h["ticker"]: h["qty"] for h in data1["holdings"]}
    tickers2 = {h["ticker"]: h["qty"] for h in data2["holdings"]}
    assert tickers1 == tickers2


@pytest.mark.asyncio
async def test_portfolio_without_auth(setup_database):
    """Test portfolio endpoint requires authentication"""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        response = await ac.get("/portfolio")
    
    assert response.status_code == 403