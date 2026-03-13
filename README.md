# M2M Bookings MCP

FastAPI server that collects booking and customer data via Zapier webhooks. It communicates with [m2m-proxy](../m2m-proxy) (a FastAPI proxy) instead of Launch27 directly, stores data in PostgreSQL, and integrates with Gmail, Klaviyo, and Zapier for notifications and CRM.

Includes MCP (Model Context Protocol) support so AI assistants like Claude Desktop can query the booking database directly.

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL database
- A `.env` file with configuration (see below)
- [pyenv](https://github.com/pyenv/pyenv) (recommended for virtualenv management)

### Create and activate the virtualenv

```bash
pyenv virtualenv 3.12.0 venv-bookings-mcp
pyenv local venv-bookings-mcp
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configuration

Configuration is managed via environment variables loaded from a `.env` file using `pydantic_settings.BaseSettings` (see `app/core/config.py`).

Key variables:

| Variable | Description |
|---|---|
| `ENVIRONMENT` | `development`, `staging`, `production`, or `testing` |
| `API_KEY` | Bearer token for API authentication |
| `DATABASE_URL` | PostgreSQL connection string |
| `PROXY_URL` | URL of the m2m-proxy server |
| `PROXY_API_KEY` | API key for m2m-proxy |

To generate a new API key:

```bash
python app/commands/generate_key.py
```

### Run the server

```bash
python run.py
```

Production uses Uvicorn directly:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## API Endpoints

All booking endpoints require a Bearer token in the `Authorization` header.

### Booking webhook endpoints (POST, called by Zapier)

| Endpoint | Description |
|---|---|
| `POST /booking/new` | New booking created |
| `POST /booking/restored` | Cancelled booking restored |
| `POST /booking/completed` | Booking marked completed |
| `POST /booking/cancellation` | Booking cancelled |
| `POST /booking/updated` | Booking details updated |
| `POST /booking/team_changed` | Team assignment changed |

### Customer webhook endpoints (POST, called by Zapier)

| Endpoint | Description |
|---|---|
| `POST /customer/new` | New customer created |
| `POST /customer/updated` | Customer details updated |

### Query endpoints (GET)

| Endpoint | Description |
|---|---|
| `GET /` | Health check |
| `GET /booking?category=...&date=...&booking_status=...` | Search bookings by category, date, and status |
| `GET /booking/{booking_id}` | Get full booking details |
| `GET /booking/was_new_customer/{booking_id}` | Check if booking was from a new customer |
| `GET /booking/search/completed?from=...&to=...` | Search completed bookings by service date range |
| `GET /booking/service_date/search?service_date=...&email=...` | Find booking by email and service date |

### OpenAPI docs

Interactive API docs available at `http://localhost:8000/docs` when the server is running.

## MCP (Model Context Protocol)

This server exposes an MCP endpoint at `/mcp`, allowing AI assistants to query the booking database.

### Claude Desktop configuration

Add the following to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "m2m-bookings": {
      "command": "mcp-proxy",
      "args": ["http://127.0.0.1:8000/mcp"],
      "env": {}
    }
  }
}
```

### MCP Inspector

Test the MCP endpoint with:

```bash
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
```

## Architecture

### SQLModel (unified ORM + Pydantic)

Models use **SQLModel** — one class defines both the DB table and Pydantic validation. DB columns with underscore prefixes (`_created_at`) are mapped to clean Python names (`created_at`) via `sa_column_kwargs`.

### Booking model

All bookings (regular, NDIS, sales) are stored in a single `bookings` table. `BookingBase` and `Booking(BookingBase, table=True)` are both in `app/models/booking.py`, which defines all columns, webhook import logic, and custom field processing.

### Project structure

```
app/
├── main.py              # FastAPI app, MCP mount, lifespan, exception handlers
├── core/
│   ├── config.py        # pydantic_settings.BaseSettings, get_settings()
│   ├── auth.py          # Bearer token authentication
│   ├── database.py      # SQLModel engine, Session, get_db()
│   └── logging_config.py # Logging setup with Gmail error handler
├── utils/
│   ├── validation.py    # Parsing, truncation, type coercion helpers
│   ├── email_service.py # Gmail API email sending
│   ├── gmail_handler.py # Gmail OAuth2 handler for error emails
│   ├── klaviyo.py       # Klaviyo CRM integration
│   ├── local_date_time.py # Timezone utilities
│   └── locations.py     # Location lookup with caching
├── models/
│   ├── booking.py       # BookingBase + Booking(table=True), webhook import logic, custom fields
│   └── customer.py      # Customer model
├── schemas/booking.py   # Pydantic response models
├── daos/
│   ├── base.py          # BaseDAO (upsert, cancel, mark converted)
│   ├── booking.py       # BookingDAO (search, date range queries)
│   └── customer.py      # CustomerDAO
├── services/
│   ├── bookings.py      # Booking business logic (update_table, search helpers)
│   └── customers.py     # Customer business logic
├── routers/
│   ├── bookings.py      # /booking/* endpoints
│   ├── customers.py     # /customer/* endpoints
│   └── health.py        # Health check
├── commands/            # Scheduled command scripts
│   └── completed/       # Mark today's bookings as completed (run via cron/Heroku Scheduler)
├── database/
│   ├── create_db.py             # One-time table creation
│   └── missing_locations.py     # Report bookings with NULL location; emails SUPPORT_EMAIL
└── templates/           # HTML email templates
scripts/
└── copy_old_db.py       # One-time migration: copy data from old DB to new DB
tests/
└── test_missing_locations.py    # pytest-asyncio tests for missing_locations script
```

## Database scripts

Standalone async scripts that open their own DB session (no HTTP request needed).

### Report bookings with missing locations

```bash
python -m app.database.missing_locations
```

Queries all bookings with a NULL `location`, deduplicates the affected postcodes, and emails a summary to `SUPPORT_EMAIL`. Safe to run anytime; email is suppressed in `testing` mode.

### Create database tables (first-time setup only)

```bash
python -m app.database.create_db
```

## Testing

```bash
pytest
```

Tests live in `tests/`. They use `pytest-asyncio` and mock all external dependencies (database, email), so no live connections are required.

To run a specific test file:

```bash
pytest tests/test_missing_locations.py -v
```

## Deployment

Heroku-based. The `Procfile` runs:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The `DATABASE_URL` env var is provided by Heroku Postgres (the app auto-corrects `postgres://` to `postgresql://`).

## Dependencies

FastAPI, Uvicorn, SQLModel 0.0.22+, Pydantic 2.9+, SQLAlchemy 2.0+, PostgreSQL (psycopg2), httpx, tenacity, cachetools, pendulum, fastapi-mcp. Full list in `requirements.txt`.
