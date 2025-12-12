from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # App
    DEBUG: bool = False
    APP_NAME: str = "Portfolio API"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://portfolio:portfolio@db:5432/portfolio"

    # Auth
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ETL Configuration
    TICKER_API_SOURCE: str = "yfinance"
    TICKERS: str = "AAPL,GOOGL,MSFT,TSLA,NVDA"  
    ETL_USE_MOCK_DATA: bool = False     
    ETL_SCHEDULE_ENABLED: bool = False
    ETL_SCHEDULE_CRON: str = "0 */6 * * *"  # Every 6 hours

    GOOGLE_CLIENT_ID: str = "mock-google-client-id"
    FACEBOOK_APP_ID: str = "mock-facebook-app-id"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="forbid"  # keeps it strict — now safe because we declared all fields
    )

    @property
    def tickers_list(self) -> List[str]:
        """Convert comma-separated TICKERS string into a clean list"""
        return [ticker.strip() for ticker in self.TICKERS.split(",") if ticker.strip()]


# Create the settings instance
settings = Settings()