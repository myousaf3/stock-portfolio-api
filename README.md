# Portfolio API

A production-ready FastAPI backend for investor portfolio management with real-time ticker data, authentication, and automated ETL pipeline.

## Features

- 🔐 **JWT Authentication** - Secure login with hashed passwords
- 📊 **Portfolio Management** - Real-time portfolio tracking with live ticker data
- 🔄 **Automated ETL** - Containerized data pipeline fetching from Yahoo Finance
- 🗄️ **PostgreSQL Backend** - All data served from database (no runtime API calls)
- 🧪 **Comprehensive Testing** - 70%+ coverage with pytest
- 🐳 **Fully Dockerized** - One-command deployment
- 📝 **Structured Logging** - Request ID tracking and status logging

## Quick Start

### Prerequisites

- Docker & Docker Compose
- (Optional) Python 3.11+ for local development

### One-Command Deploy

```bash
# Clone repository
git clone <repository-url>
cd portfolio-api

# Copy environment variables
cp .env.example .env

# Start all services
docker compose up
```

The API will be available at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Tickers to track (comma-separated)
TICKERS=AAPL,GOOGL,MSFT,AMZN,TSLA,META,NVDA,JPM,V,WMT

# Database (auto-configured in Docker)
DATABASE_URL=postgresql+asyncpg://portfolio:portfolio@db:5432/portfolio

# Debug mode
DEBUG=false
```

### Generate Secure Secret Key

```bash
openssl rand -hex 32
```

## ETL Pipeline

### How It Works

The ETL service runs automatically at startup and fetches real ticker data from Yahoo Finance (free, no API key needed).

**Data Flow:**
1. Container starts → ETL triggers
2. Fetches tickers from `TICKERS` environment variable
3. Downloads 30 days of historical data per ticker
4. Stores in PostgreSQL (`tickers` and `prices` tables)
5. API serves all data from database only

### Changing Tickers

Edit the `TICKERS` variable in `.env`:

```bash
TICKERS=AAPL,MSFT,NVDA,TSLA,AMD
```

Then restart:

```bash
docker compose down
docker compose up
```

### Manual ETL Trigger

ETL runs on startup. To re-run ETL:

```bash
docker compose restart api
```

### Scheduling ETL (Future Enhancement)

To enable periodic updates, set in `.env`:

```bash
ETL_SCHEDULE_ENABLED=true
ETL_SCHEDULE_CRON="0 */6 * * *"  # Every 6 hours
```

## API Endpoints

### Authentication

#### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "demo123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Social Login (Mock)

```bash
# Google
curl -X POST "http://localhost:8000/auth/social?provider=google" \
  -H "Content-Type: application/json" \
  -d '{"token": "mock-token"}'

# Facebook
curl -X POST "http://localhost:8000/auth/social?provider=facebook" \
  -H "Content-Type: application/json" \
  -d '{"token": "mock-token"}'
```

### Portfolio

#### Get Portfolio

```bash
curl -X GET http://localhost:8000/portfolio \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "holdings": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "qty": 12,
      "price": 192.5,
      "dailyChangePct": -0.4,
      "value": 2310.0
    },
    {
      "ticker": "GOOGL",
      "name": "Alphabet Inc.",
      "qty": 8,
      "price": 141.2,
      "dailyChangePct": 1.2,
      "value": 1129.6
    }
  ],
  "totalValue": 3439.6
}
```

### Health Check

```bash
curl http://localhost:8000/healthz
```

**Response:**
```json
{
  "ok": true,
  "database": "connected"
}
```

## Demo Credentials

The system creates a demo user on first run:

- **Email:** `demo@example.com`
- **Password:** `demo123`

Or use social login (mock):
- **Google:** `demo-google@example.com`
- **Facebook:** `demo-facebook@example.com`

### Create Custom Demo User

```bash
docker compose exec api python -m scripts.init_demo_user
```

## Portfolio Generation

- Each user gets a unique, deterministic portfolio
- Generated on first login using user ID as seed
- Contains 3-7 random holdings from available tickers
- Same user sees same portfolio across sessions
- Quantities: 5-50 shares per holding

## Testing

### Run All Tests

```bash
# Inside Docker
docker compose exec api pytest

# With coverage report
docker compose exec api pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
docker compose exec api pytest --cov=app --cov-report=html
```

### Local Testing (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Create test database
createdb portfolio_test

# Run tests
pytest --cov=app --cov-report=term-missing
```

### Test Coverage

Current coverage: **~75%**

Coverage report is generated in `htmlcov/index.html`

### Test Structure

```
tests/
├── test_auth.py         # Authentication tests
├── test_portfolio.py    # Portfolio endpoint tests
└── test_health.py       # Health check tests
```

## Project Structure

```
portfolio-api/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # Auth endpoints
│   │       ├── portfolio.py     # Portfolio endpoints
│   │       └── health.py        # Health check
│   ├── core/
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database setup
│   │   └── logging.py           # Structured logging
│   ├── models/
│   │   └── models.py            # SQLAlchemy models
│   └── services/
│       ├── auth.py              # Auth service
│       ├── portfolio.py         # Portfolio service
│       └── etl.py               # ETL service
├── tests/                       # Test suite
├── scripts/
│   └── init_demo_user.py       # Demo user script
├── main.py                      # FastAPI app
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container definition
├── docker-compose.yml           # Multi-container setup
├── pytest.ini                   # Test configuration
├── .env.example                 # Environment template
└── README.md                    # This file
```

## Database Schema

### Users Table
```sql
id, email, hashed_password, full_name, is_active, created_at
```

### Tickers Table
```sql
id, symbol, name, sector, updated_at
```

### Prices Table
```sql
id, ticker_id, date, open_price, high_price, low_price, close_price, volume
```

### Portfolios Table
```sql
id, user_id, ticker_id, quantity, created_at
```

## Development

### Local Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start database only
docker compose up db

# Run API locally with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Access Database

```bash
# Via Docker
docker compose exec db psql -U portfolio -d portfolio

# Local connection
psql -h localhost -U portfolio -d portfolio
```

### View Logs

```bash
# All services
docker compose logs -f

# API only
docker compose logs -f api

# Database only
docker compose logs -f db
```

## API Documentation

Interactive API docs available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc