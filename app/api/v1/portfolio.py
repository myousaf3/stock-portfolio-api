import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.models import User
from app.services.portfolio import PortfolioService
from app.core.logging import set_request_id

logger = logging.getLogger(__name__)
router = APIRouter()


class HoldingResponse(BaseModel):
    ticker: str
    name: str
    qty: int
    price: float
    dailyChangePct: float
    value: float


class PortfolioResponse(BaseModel):
    holdings: List[HoldingResponse]
    totalValue: float


@router.get("", response_model=PortfolioResponse)
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's portfolio with current prices"""
    set_request_id()
    logger.info(f"Fetching portfolio for user: {current_user.email}")
    
    portfolio_service = PortfolioService(db)
    portfolio_data = await portfolio_service.get_user_portfolio(current_user.id)
    
    logger.info(
        f"Portfolio retrieved for {current_user.email}: "
        f"{len(portfolio_data['holdings'])} holdings, "
        f"total value: ${portfolio_data['totalValue']:.2f}"
    )
    
    return portfolio_data
