# Portfolio API - cURL Examples

Complete examples for testing all API endpoints.

## Setup

First, start the services:

```bash
docker compose up
```

Wait for the message: "ETL completed successfully"

## 1. Health Check

Test that the API is running:

```bash
curl http://localhost:8000/healthz
```

**Expected Response:**
```json
{
  "ok": true,
  "database": "connected"
}
```

## 2. Login

### Standard Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "demo123"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJkZW1vQGV4YW1wbGUuY29tIiwiZXhwIjoxNzAwMDAwMDAwfQ.xxxxx",
  "token_type": "bearer"
}
```

### Save Token to Variable (Bash)

```bash
# Login and save token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "demo123"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

### Login with Invalid Credentials

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "wrong@example.com",
    "password": "wrongpassword"
  }'
```

**Expected Response:**
```json
{
  "detail": "Incorrect email or password"
}
```

## 3. Social Authentication

### Google Login (Mock)

```bash
curl -X POST "http://localhost:8000/auth/social?provider=google" \
  -H "Content-Type: application/json" \
  -d '{"token": "mock-google-token"}'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "provider": "google"
}
```

### Facebook Login (Mock)

```bash
curl -X POST "http://localhost:8000/auth/social?provider=facebook" \
  -H "Content-Type: application/json" \
  -d '{"token": "mock-facebook-token"}'
```

### Invalid Provider

```bash
curl -X POST "http://localhost:8000/auth/social?provider=twitter" \
  -H "Content-Type: application/json" \
  -d '{"token": "mock-token"}'
```

**Expected Response:**
```json
{
  "detail": "Invalid provider. Must be 'google' or 'facebook'"
}
```

## 4. Portfolio

### Get Portfolio (Authenticated)

First, get a token:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo123"}' \
  | jq -r '.access_token')
```

Then request portfolio:

```bash
curl -X GET http://localhost:8000/portfolio \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "holdings": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "qty": 25,
      "price": 192.53,
      "dailyChangePct": -0.42,
      "value": 4813.25
    },
    {
      "ticker": "GOOGL",
      "name": "Alphabet Inc.",
      "qty": 15,
      "price": 141.80,
      "dailyChangePct": 1.25,
      "value": 2127.00
    },
    {
      "ticker": "MSFT",
      "name": "Microsoft Corporation",
      "qty": 20,
      "price": 378.91,
      "dailyChangePct": 0.87,
      "value": 7578.20
    }
  ],
  "totalValue": 14518.45
}
```

### Get Portfolio Without Token

```bash
curl -X GET http://localhost:8000/portfolio
```

**Expected Response:**
```json
{
  "detail": "Not authenticated"
}
```

### Get Portfolio with Invalid Token

```bash
curl -X GET http://localhost:8000/portfolio \
  -H "Authorization: Bearer invalid-token-here"
```

**Expected Response:**
```json
{
  "detail": "Invalid or expired token"
}
```

## 5. Pretty Print with jq

If you have `jq` installed, you can pretty-print responses:

```bash
# Health check
curl -s http://localhost:8000/healthz | jq

# Login
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo123"}' | jq

# Portfolio
curl -s -X GET http://localhost:8000/portfolio \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 6. Complete Workflow Example

```bash
#!/bin/bash

echo "=== Portfolio API Test Workflow ==="
echo ""

# 1. Health Check
echo "1. Checking API health..."
curl -s http://localhost:8000/healthz | jq
echo ""

# 2. Login
echo "2. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demo123"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "✅ Logged in successfully"
echo "Token: ${TOKEN:0:50}..."
echo ""

# 3. Get Portfolio
echo "3. Fetching portfolio..."
PORTFOLIO=$(curl -s -X GET http://localhost:8000/portfolio \
  -H "Authorization: Bearer $TOKEN")

echo "$PORTFOLIO" | jq
echo ""

# 4. Display Summary
TOTAL_VALUE=$(echo $PORTFOLIO | jq -r '.totalValue')
NUM_HOLDINGS=$(echo $PORTFOLIO | jq '.holdings | length')

echo "=== Portfolio Summary ==="
echo "Total Holdings: $NUM_HOLDINGS"
echo "Total Value: \$$TOTAL_VALUE"
echo ""

# 5. List all tickers
echo "Holdings:"
echo "$PORTFOLIO" | jq -r '.holdings[] | "\(.ticker): \(.qty) shares @ $\(.price) = $\(.value)"'
```

Save as `test_workflow.sh`, make executable, and run:

```bash
chmod +x test_workflow.sh
./test_workflow.sh
```

## 7. Testing Different Users

Each user gets a unique portfolio. Test with social logins:

```bash
# Login as Google user
GOOGLE_TOKEN=$(curl -s -X POST "http://localhost:8000/auth/social?provider=google" \
  -H "Content-Type: application/json" \
  -d '{"token": "mock-token"}' | jq -r '.access_token')

# Get Google user's portfolio
curl -s -X GET http://localhost:8000/portfolio \
  -H "Authorization: Bearer $GOOGLE_TOKEN" | jq

# Login as Facebook user
FACEBOOK_TOKEN=$(curl -s -X POST "http://localhost:8000/auth/social?provider=facebook" \
  -H "Content-Type: application/json" \
  -d '{"token": "mock-token"}' | jq -r '.access_token')

# Get Facebook user's portfolio
curl -s -X GET http://localhost:8000/portfolio \
  -H "Authorization: Bearer $FACEBOOK_TOKEN" | jq
```

You'll see each user has different holdings!

## 8. Error Handling Examples

### Missing Fields

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com"}'
```

### Invalid Email Format

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"not-an-email","password":"demo123"}'
```

### Expired Token

Tokens expire after 30 minutes by default. After expiration:

```bash
curl -X GET http://localhost:8000/portfolio \
  -H "Authorization: Bearer expired-token"
```

## 9. Performance Testing

### Simple Load Test

```bash
# Run 100 requests
for i in {1..100}; do
  curl -s http://localhost:8000/healthz > /dev/null
  echo "Request $i completed"
done
```

### With Apache Bench (if installed)

```bash
# 1000 requests, 10 concurrent
ab -n 1000 -c 10 http://localhost:8000/healthz
```

## 10. Debugging

### Verbose Output

```bash
curl -v http://localhost:8000/healthz
```

### Include Response Headers

```bash
curl -i http://localhost:8000/healthz
```

### Save Response to File

```bash
curl -s http://localhost:8000/portfolio \
  -H "Authorization: Bearer $TOKEN" \
  -o portfolio.json

cat portfolio.json | jq
```

## Notes

- All timestamps in responses are in UTC
- Tokens expire after 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Portfolio data refreshes when ETL runs (on startup by default)
- Daily change percentage compares to previous day's close price
- All monetary values in USD

## Troubleshooting

If endpoints return errors:

1. **Connection refused**: Ensure services are running
   ```bash
   docker compose ps
   ```

2. **Invalid token**: Token may be expired, login again
   ```bash
   TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"demo@example.com","password":"demo123"}' \
     | jq -r '.access_token')
   ```

3. **No data returned**: ETL may still be running, check logs
   ```bash
   docker compose logs api
   ```
