# Quantfox - Price Aggregation System

A microservices-based backend system for computing daily average prices, built with Rust and Python.

## Architecture

```
                         ┌─────────────────┐
                         │     Client      │
                         └────────┬────────┘
                                  │ HTTP
                                  ▼
┌──────────────────────────────────────────────────────────────┐
│                      rust-api (:8000)                        │
│  - Validates date parameters (ISO 8601)                      │
│  - Forwards requests to python-api                           │
│  - Returns structured JSON responses                         │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTP
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                    python-api (:8001)                        │
│  - Validates dates independently                             │
│  - Triggers Celery task for computation                      │
│  - Waits synchronously for task result                       │
└────────────────────────────┬─────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌─────────────────────┐         ┌─────────────────────┐
│   celery-worker     │◄───────►│   redis (:6379)     │
│   (background task) │ broker  │   (Celery broker)   │
└──────────┬──────────┘         └─────────────────────┘
           │ SQL (aggregation)
           ▼
┌─────────────────────┐
│  postgres (:5432)   │
│  (prices table)     │
└─────────────────────┘
```

### Celery Task Strategy

The system uses **synchronous task execution**: the HTTP handler waits for the Celery task result directly (`.get(timeout=60)`). This approach was chosen for simplicity and predictability - each request returns the complete result immediately.

### Database Optimization

Daily average computation is performed at the database level using SQL `GROUP BY` aggregation, avoiding memory-intensive processing in Python:

```sql
SELECT DATE(recorded_at) as date, AVG(price) as average_price
FROM prices
WHERE DATE(recorded_at) >= %s AND DATE(recorded_at) <= %s
GROUP BY DATE(recorded_at)
ORDER BY date
```

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Quantfox
   ```

2. **Start all services**
   ```bash
   docker compose up --build
   ```

   This command will:
   - Build the Rust and Python Docker images
   - Start PostgreSQL with automatic schema initialization
   - Seed the database with sample price data (Jan 1-5, 2025)
   - Start Redis as the Celery broker
   - Launch the Python API and Celery worker
   - Launch the Rust API (public endpoint)

3. **Wait for services to be ready** (approximately 1-2 minutes for first build)

4. **Test the API**
   ```bash
   curl "http://localhost:8000/prices/average?start_date=2025-01-01&end_date=2025-01-05"
   ```

## API Reference

### Health Check

Both services expose a health check endpoint:

```bash
# Rust API
curl http://localhost:8000/health
# Response: {"status":"healthy","service":"rust-api"}

# Python API
curl http://localhost:8001/health
# Response: {"status":"healthy","service":"python-api"}
```

### API Documentation (Swagger)

The Python API provides interactive documentation:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Main Endpoint

```
GET /prices/average
```

### Query Parameters

| Parameter    | Required | Format     | Description                    |
|-------------|----------|------------|--------------------------------|
| start_date  | Yes      | YYYY-MM-DD | Start date (ISO 8601)          |
| end_date    | Yes      | YYYY-MM-DD | End date (inclusive, ISO 8601) |

### Success Response (200)

```json
{
  "data": [
    {"date": "2024-01-01", "average_price": 98.45},
    {"date": "2024-01-02", "average_price": 102.33},
    {"date": "2024-01-03", "average_price": 99.87}
  ]
}
```

### Error Responses

All error responses follow the same structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```

| Status | Code                 | Description                          |
|--------|---------------------|--------------------------------------|
| 400    | MISSING_PARAMETER   | Required parameter not provided      |
| 400    | INVALID_DATE_FORMAT | Date not in YYYY-MM-DD format        |
| 400    | INVALID_DATE_RANGE  | start_date is after end_date         |
| 500    | INTERNAL_ERROR      | Server-side error                    |
| 502    | UPSTREAM_ERROR      | Python API or Celery task failure    |

### Example Requests

**Valid request:**
```bash
curl "http://localhost:8000/prices/average?start_date=2024-02-01&end_date=2024-02-28"
```

**Missing parameter (400):**
```bash
curl "http://localhost:8000/prices/average?start_date=2024-01-01"
# Response: {"error":{"code":"MISSING_PARAMETER","message":"Missing required parameter: end_date"}}
```

**Invalid date format (400):**
```bash
curl "http://localhost:8000/prices/average?start_date=01-01-2024&end_date=2024-01-31"
# Response: {"error":{"code":"INVALID_DATE_FORMAT","message":"Invalid date format for start_date. Expected ISO 8601 format (YYYY-MM-DD)"}}
```

**Invalid date range (400):**
```bash
curl "http://localhost:8000/prices/average?start_date=2024-01-31&end_date=2024-01-01"
# Response: {"error":{"code":"INVALID_DATE_RANGE","message":"start_date must be before or equal to end_date"}}
```

## Configuration

All configuration is stored in TOML files:

### Rust API (`rust-api/config.toml`)

```toml
[server]
host = "0.0.0.0"
port = 8000

[python_api]
url = "http://python-api:8001"
timeout_seconds = 30

[logging]
level = "info"
```

### Python API (`python-api/config.toml`)

```toml
[database]
host = "postgres"
port = 5432
name = "quantfox"
user = "quantfox"
password = "quantfox"

[celery]
broker_url = "redis://redis:6379/0"
result_backend = "redis://redis:6379/1"

[server]
host = "0.0.0.0"
port = 8001
```

## Database Schema

```sql
CREATE TABLE prices (
    id SERIAL PRIMARY KEY,
    recorded_at TIMESTAMP NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

CREATE INDEX idx_prices_recorded_at ON prices(recorded_at);
```

The database is automatically initialized and seeded when Docker Compose starts.

## Running Tests

### Python tests
```bash
cd python-api
pip install -e ".[dev]"
pytest
```

### Rust tests
```bash
cd rust-api
cargo test
```

## Project Structure

```
Quantfox/
├── docker-compose.yml          # Service orchestration
├── init.sql                    # Database schema + sample data
├── rust-api/
│   ├── Cargo.toml
│   ├── Dockerfile
│   ├── config.toml
│   └── src/
│       ├── main.rs            # Actix Web server setup
│       ├── config.rs          # TOML configuration loading
│       ├── errors.rs          # Error types and responses
│       └── handlers.rs        # Request handlers + validation
└── python-api/
    ├── pyproject.toml
    ├── Dockerfile
    ├── config.toml
    ├── app/
    │   ├── main.py            # FastAPI application
    │   ├── config.py          # TOML configuration loading
    │   ├── celery_app.py      # Celery configuration
    │   ├── tasks.py           # Celery task definitions
    │   ├── database.py        # PostgreSQL queries
    │   └── errors.py          # Error handling
    └── tests/
        └── test_validation.py # Unit tests
```

## Stopping Services

```bash
docker-compose down
```

To also remove the database volume:
```bash
docker-compose down -v
```
