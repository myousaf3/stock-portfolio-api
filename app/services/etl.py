import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import List
import yfinance as yf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.models import Ticker, Price

logger = logging.getLogger(__name__)

# Mock ticker data for when Yahoo Finance is rate-limited
MOCK_TICKER_DATA = {
    'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology', 'base_price': 192.50},
    'GOOGL': {'name': 'Alphabet Inc.', 'sector': 'Technology', 'base_price': 141.80},
    'MSFT': {'name': 'Microsoft Corporation', 'sector': 'Technology', 'base_price': 378.91},
    'TSLA': {'name': 'Tesla, Inc.', 'sector': 'Automotive', 'base_price': 242.84},
    'NVDA': {'name': 'NVIDIA Corporation', 'sector': 'Technology', 'base_price': 140.15},
    'AMZN': {'name': 'Amazon.com, Inc.', 'sector': 'Consumer Cyclical', 'base_price': 197.50},
    'META': {'name': 'Meta Platforms, Inc.', 'sector': 'Technology', 'base_price': 352.00},
    'JPM': {'name': 'JPMorgan Chase & Co.', 'sector': 'Financial Services', 'base_price': 225.00},
    'V': {'name': 'Visa Inc.', 'sector': 'Financial Services', 'base_price': 295.00},
    'WMT': {'name': 'Walmart Inc.', 'sector': 'Consumer Defensive', 'base_price': 85.00}
}


class ETLService:
    def __init__(self):
        self.use_mock_data = settings.ETL_USE_MOCK_DATA
    
    async def run_etl(self):
        """Run ETL process to fetch and store ticker data"""
        logger.info("Starting ETL process...")
        
        async with AsyncSessionLocal() as db:
            tickers_to_fetch = settings.tickers_list
            logger.info(f"Fetching data for {len(tickers_to_fetch)} tickers: {tickers_to_fetch}")
            
            # Process tickers concurrently with staggered delays
            tasks = []
            for idx, symbol in enumerate(tickers_to_fetch):
                tasks.append(self._fetch_ticker_with_delay(db, symbol, idx))
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            success_count = sum(1 for r in results if r is True)
            error_count = sum(1 for r in results if isinstance(r, Exception))
            logger.info(f"ETL process completed: {success_count} successful, {error_count} errors")
    
    async def _fetch_ticker_with_delay(self, db: AsyncSession, symbol: str, idx: int):
        """Fetch ticker with staggered delay to avoid rate limiting"""
        try:
            # Stagger requests to avoid overwhelming the API
            await asyncio.sleep(idx * 0.5)
            
            if self.use_mock_data:
                await self._create_mock_data(db, symbol)
            else:
                await self._fetch_and_store_ticker(db, symbol)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing ticker {symbol}: {str(e)}")
            if "429" in str(e) or "Too Many Requests" in str(e) or "Expecting value" in str(e):
                logger.warning(f"API error detected for {symbol}. Switching to mock data.")
                self.use_mock_data = True
                try:
                    await self._create_mock_data(db, symbol)
                    return True
                except Exception as mock_error:
                    logger.error(f"Failed to create mock data for {symbol}: {mock_error}")
                    return mock_error
            return e
    
    async def _create_mock_data(self, db: AsyncSession, symbol: str):
        """Create mock data for a ticker when API is unavailable"""
        logger.info(f"Creating mock data for ticker: {symbol}")
        
        # Get mock data or use defaults
        mock_info = MOCK_TICKER_DATA.get(symbol, {
            'name': f'{symbol} Inc.',
            'sector': 'Unknown',
            'base_price': 100.0
        })
        
        # Get or create ticker record
        result = await db.execute(
            select(Ticker).where(Ticker.symbol == symbol)
        )
        db_ticker = result.scalar_one_or_none()
        
        if not db_ticker:
            db_ticker = Ticker(
                symbol=symbol,
                name=mock_info['name'],
                sector=mock_info['sector']
            )
            db.add(db_ticker)
            await db.commit()
            await db.refresh(db_ticker)
            logger.info(f"Created ticker with mock data: {symbol} - {db_ticker.name}")
        else:
            logger.info(f"Ticker already exists: {symbol}")
        
        # Generate mock price data (last 30 days)
        base_price = mock_info['base_price']
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Optimize: Fetch all existing dates upfront
        existing_dates_result = await db.execute(
            select(Price.date).where(Price.ticker_id == db_ticker.id)
        )
        existing_dates_set = {d[0].date() for d in existing_dates_result.fetchall()}
        
        prices_added = 0
        current_date = start_date
        current_price = base_price * random.uniform(0.95, 1.05)
        prices_to_add = []
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            # Check if price already exists using the set
            if current_date.date() not in existing_dates_set:
                # Generate realistic daily price movement
                daily_change = random.uniform(-0.03, 0.03)  # ±3% daily change
                current_price = current_price * (1 + daily_change)
                
                # Generate OHLC data
                open_price = current_price * random.uniform(0.99, 1.01)
                high_price = max(open_price, current_price) * random.uniform(1.0, 1.02)
                low_price = min(open_price, current_price) * random.uniform(0.98, 1.0)
                close_price = current_price
                volume = int(random.uniform(50_000_000, 150_000_000))
                
                price = Price(
                    ticker_id=db_ticker.id,
                    date=current_date,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=volume
                )
                prices_to_add.append(price)
                prices_added += 1
            
            current_date += timedelta(days=1)
        
        # Bulk add all prices
        if prices_to_add:
            db.add_all(prices_to_add)
            await db.commit()
        
        logger.info(f"Created {prices_added} mock price records for {symbol}")
    
    async def _fetch_and_store_ticker(self, db: AsyncSession, symbol: str):
        """Fetch and store data for a single ticker"""
        logger.info(f"Processing ticker: {symbol}")
        
        try:
            # Fetch ticker info and historical data
            ticker = yf.Ticker(symbol)
            
            # Add delay before fetching info
            await asyncio.sleep(1)
            info = ticker.info
            
            # Get or create ticker record
            result = await db.execute(
                select(Ticker).where(Ticker.symbol == symbol)
            )
            db_ticker = result.scalar_one_or_none()
            
            if not db_ticker:
                db_ticker = Ticker(
                    symbol=symbol,
                    name=info.get('longName', symbol),
                    sector=info.get('sector', 'Unknown')
                )
                db.add(db_ticker)
                await db.commit()
                await db.refresh(db_ticker)
                logger.info(f"Created ticker: {symbol} - {db_ticker.name}")
            else:
                # Update ticker info
                db_ticker.name = info.get('longName', db_ticker.name)
                db_ticker.sector = info.get('sector', db_ticker.sector)
                db_ticker.updated_at = datetime.utcnow()
                await db.commit()
                logger.info(f"Updated ticker: {symbol}")
            
            # Fetch historical data (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            await asyncio.sleep(1)  # Delay before history fetch
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                logger.warning(f"No historical data for {symbol}, using mock data")
                raise ValueError("No historical data available")
            
            # Optimize: Fetch existing dates upfront
            existing_dates_result = await db.execute(
                select(Price.date).where(Price.ticker_id == db_ticker.id)
            )
            existing_dates_set = {d[0].date() for d in existing_dates_result.fetchall()}
            
            # Store price data with bulk insert
            prices_to_add = []
            for date, row in hist.iterrows():
                date_obj = date.to_pydatetime()
                
                # Check if price already exists using the set
                if date_obj.date() not in existing_dates_set:
                    price = Price(
                        ticker_id=db_ticker.id,
                        date=date_obj,
                        open_price=float(row['Open']),
                        high_price=float(row['High']),
                        low_price=float(row['Low']),
                        close_price=float(row['Close']),
                        volume=int(row['Volume'])
                    )
                    prices_to_add.append(price)
            
            # Bulk add all prices
            if prices_to_add:
                db.add_all(prices_to_add)
                await db.commit()
            
            logger.info(f"Stored {len(prices_to_add)} price records for {symbol}")
            
        except Exception as e:
            logger.warning(f"Failed to fetch real data for {symbol}: {str(e)}")
            raise  