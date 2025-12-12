import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel

from app.core.database import get_db
from app.core.logging import set_request_id

logger = logging.getLogger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    ok: bool
    database: str = "connected"


@router.get("/healthz", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    set_request_id()
    
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        logger.debug("Health check passed")
        return HealthResponse(ok=True)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(ok=False, database="disconnected")
