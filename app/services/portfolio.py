import logging
import random
from typing import Dict, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.models import Portfolio, Ticker, Price, User

logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_portfolio(self, user_id: int) -> Dict:
        """Get user's portfolio with current prices"""
        # Check if user has portfolio
        result = await self.db.execute(
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .options(joinedload(Portfolio.ticker))
        )
        holdings = result.scalars().all()
        
        # If no portfolio exists, create one
        if not holdings:
            await self._generate_portfolio(user_id)
            result = await self.db.execute(
                select(Portfolio)
                .where(Portfolio.user_id == user_id)
                .options(joinedload(Portfolio.ticker))
            )
            holdings = result.scalars().all()
        
        if not holdings:
            return {"holdings": [], "totalValue": 0.0}
        
        # Optimize: Fetch all prices in a single query using window function
        ticker_ids = [holding.ticker_id for holding in holdings]
        
        # Subquery to get row numbers for each price ordered by date descending
        from sqlalchemy import literal_column
        price_with_row_num = (
            select(
                Price,
                func.row_number().over(
                    partition_by=Price.ticker_id,
                    order_by=Price.date.desc()
                ).label('row_num')
            )
            .where(Price.ticker_id.in_(ticker_ids))
            .subquery()
        )
        
        # Get latest (row_num=1) and previous (row_num=2) prices
        prices_result = await self.db.execute(
            select(price_with_row_num)
            .where(price_with_row_num.c.row_num.in_([1, 2]))
        )
        prices_rows = prices_result.all()
        
        # Organize prices by ticker_id
        prices_by_ticker = {}
        for row in prices_rows:
            ticker_id = row.ticker_id
            if ticker_id not in prices_by_ticker:
                prices_by_ticker[ticker_id] = {}
            
            if row.row_num == 1:
                prices_by_ticker[ticker_id]['latest'] = row
            elif row.row_num == 2:
                prices_by_ticker[ticker_id]['previous'] = row
        
        # Build portfolio response
        portfolio_holdings = []
        total_value = 0.0
        
        for holding in holdings:
            ticker = holding.ticker
            ticker_prices = prices_by_ticker.get(ticker.id, {})
            
            latest_price = ticker_prices.get('latest')
            if not latest_price:
                continue
            
            prev_price = ticker_prices.get('previous')
            
            # Calculate daily change
            if prev_price and prev_price.close_price:
                daily_change_pct = (
                    (latest_price.close_price - prev_price.close_price) 
                    / prev_price.close_price * 100
                )
            else:
                daily_change_pct = 0.0
            
            value = latest_price.close_price * holding.quantity
            total_value += value
            
            portfolio_holdings.append({
                "ticker": ticker.symbol,
                "name": ticker.name,
                "qty": holding.quantity,
                "price": round(latest_price.close_price, 2),
                "dailyChangePct": round(daily_change_pct, 2),
                "value": round(value, 2)
            })
        
        return {
            "holdings": portfolio_holdings,
            "totalValue": round(total_value, 2)
        }
    
    async def _generate_portfolio(self, user_id: int):
        """Generate a deterministic portfolio for a user"""
        # Get all available tickers
        result = await self.db.execute(select(Ticker))
        tickers = result.scalars().all()
        
        if not tickers:
            logger.warning("No tickers available to generate portfolio")
            return
        
        # Use user_id as seed for deterministic generation
        random.seed(user_id)
        
        # Select 3-7 random tickers
        num_holdings = random.randint(3, min(7, len(tickers)))
        selected_tickers = random.sample(tickers, num_holdings)
        
        # Create portfolio holdings with random quantities
        for ticker in selected_tickers:
            quantity = random.randint(5, 50)
            
            portfolio = Portfolio(
                user_id=user_id,
                ticker_id=ticker.id,
                quantity=quantity
            )
            self.db.add(portfolio)
        
        await self.db.commit()
        logger.info(f"Generated portfolio for user {user_id} with {num_holdings} holdings")
        
        # Reset random seed
        random.seed()
