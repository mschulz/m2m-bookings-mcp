# M2M Bookings MCP

FastAPI server that collects booking data from Launch27 via Zapier webhooks. It communicates with [m2m-proxy](../m2m-proxy) (a FastAPI proxy) instead of Launch27 directly, stores bookings in PostgreSQL, and integrates with Gmail and Klaviyo for notifications and CRM.

Includes MCP (Model Context Protocol) support so AI assistants like Claude Desktop can query the booking database directly.

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL database
- A `.env` file with configuration (see below)

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configuration

Configuration is managed via environment variables loaded from a `.env` file using `pydantic_settings.BaseSettings` (see `config.py`).

Key variables:

| Variable | Description |
|---|---|
| `ENVIRONMENT` | `development`, `staging`, `production`, or `testing` |
| `API_KEY` | Bearer token for API authentication |
| `DATABASE_URL` | PostgreSQL connection string |
| `PROXY_URL` | URL of the m2m-proxy server |
| `PROXY_API_KEY` | API key for m2m-proxy |
| `PROXY_USERNAME` | Proxy login username |
| `PROXY_PASSWORD` | Proxy login password |

To generate a new API key:

```bash
python generate_key.py
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

### Webhook endpoints (POST, called by Zapier)

| Endpoint | Description |
|---|---|
| `POST /booking/new` | New booking created |
| `POST /booking/restored` | Cancelled booking restored |
| `POST /booking/completed` | Booking marked completed |
| `POST /booking/cancellation` | Booking cancelled |
| `POST /booking/updated` | Booking details updated |
| `POST /booking/team_changed` | Team assignment changed |

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

### Booking types (separate DB tables, shared base model)

- **Booking** — regular cleaning bookings
- **Reservation** — NDIS reservations
- **SalesReservation** — sales reservations

All inherit from `BookingBase` in `app/models/base.py`.

### Project structure

```
app/
├── main.py              # FastAPI app, MCP mount, lifespan, exception handlers
├── database.py          # SQLAlchemy engine, sessionmaker, get_db()
├── auth.py              # Bearer token authentication
├── logging_config.py    # Logging setup with Gmail error handler
├── gmail_handler.py     # Gmail OAuth2 handler for error emails
├── local_date_time.py   # Timezone utilities
├── utils/validation.py  # Field truncation, type coercion, postcode checks
├── models/
│   ├── base.py          # BookingBase with all columns and hybrid properties
│   ├── booking.py       # Booking, Reservation, SalesReservation models
│   ├── customer.py      # Customer model
│   └── cancellation.py  # Cancellation import helper
├── schemas/booking.py   # Pydantic request/response models
├── daos/
│   ├── base.py          # BaseDAO (upsert, cancel, mark converted)
│   ├── booking.py       # BookingDAO (search, date range queries)
│   ├── customer.py      # CustomerDAO
│   ├── reservation.py   # ReservationDAO
│   └── sales_reservation.py
├── routers/
│   ├── bookings.py      # /booking/* endpoints
│   └── health.py        # Health check
├── services/
│   ├── klaviyo.py       # Klaviyo CRM integration
│   ├── notifications.py # Webhook notifications
│   ├── locations.py     # Location lookup with caching
│   └── email_service.py # Gmail API email sending
├── database/            # Utility scripts (create_db, update_durations, etc.)
├── commands/            # Scheduled command scripts
└── templates/           # HTML email templates
```

## Deployment

Heroku-based. The `Procfile` runs:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The `DATABASE_URL` env var is provided by Heroku Postgres (the app auto-corrects `postgres://` to `postgresql://`).

## Dependencies

FastAPI, Uvicorn, Pydantic 2.9+, SQLAlchemy 2.0+, PostgreSQL (psycopg2), httpx, tenacity, cachetools, pendulum, fastapi-mcp. Full list in `requirements.txt`.
