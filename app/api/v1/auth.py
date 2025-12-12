import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.services.auth import AuthService
from app.core.logging import set_request_id

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SocialAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    provider: str


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password"""
    set_request_id()
    logger.info(f"Login attempt for user: {request.email}")
    
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(request.email, request.password)
    
    if not user:
        logger.warning(f"Failed login attempt for: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = auth_service.create_access_token(user.id, user.email)
    logger.info(f"Successful login for user: {request.email}")
    
    return LoginResponse(access_token=access_token)


@router.post("/social", response_model=SocialAuthResponse)
async def social_login(
    provider: str,
    token: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Mock social authentication (Google/Facebook)"""
    set_request_id()
    logger.info(f"Social login attempt with provider: {provider}")
    
    if provider not in ["google", "facebook"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider. Must be 'google' or 'facebook'"
        )
    
    # Mock social auth - in production, verify token with provider
    auth_service = AuthService(db)
    mock_email = f"demo-{provider}@example.com"
    
    # Get or create user
    user = await auth_service.get_user_by_email(mock_email)
    if not user:
        user = await auth_service.create_user(
            email=mock_email,
            password="mock-password-not-used",
            full_name=f"Demo {provider.title()} User"
        )
        logger.info(f"Created new user via {provider}: {mock_email}")
    
    access_token = auth_service.create_access_token(user.id, user.email)
    logger.info(f"Successful {provider} login for: {mock_email}")
    
    return SocialAuthResponse(
        access_token=access_token,
        provider=provider
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Verify JWT token and return current user"""
    set_request_id()
    
    auth_service = AuthService(db)
    user = await auth_service.verify_token(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return user
