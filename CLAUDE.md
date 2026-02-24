# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI server that collects booking data via Zapier webhooks, communicating with m2m-proxy (a FastAPI proxy at `../m2m-proxy`) instead of Launch27 directly. It stores bookings in PostgreSQL and integrates with Gmail, Slack, Klaviyo, and Zapier for notifications and CRM.

## Running the Application

```bash
python run.py
```

Production uses Uvicorn: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Configuration

- Uses `pydantic_settings.BaseSettings` in `config.py` with `.env` file
- `ENVIRONMENT` field (development/staging/production/testing) controls behavior
- Computed properties: `debug`, `testing`, `log_to_stdout` derived from `ENVIRONMENT`
- `testing=True` suppresses email sending
- API authentication via Bearer token in Authorization header, validated against `API_KEY`
- Proxy config: `PROXY_URL`, `PROXY_API_KEY`, `PROXY_USERNAME`, `PROXY_PASSWORD`
- Settings singleton via `@lru_cache` on `get_settings()`

## Architecture

**DAO Pattern:** Routes stay thin, calling DAO methods directly. DAOs are module-level singletons. All DAO methods accept a `db: Session` parameter injected via FastAPI's `Depends(get_db)`.

### Request Flow (webhook from Zapier)
1. POST hits route (e.g., `/booking/new`)
2. `verify_api_key` FastAPI dependency validates Bearer token
3. FastAPI exception handlers catch DB connection drops (503) and data errors (422)
4. Route parses JSON body, calls `update_table()` which routes to the correct DAO based on `service_category`
5. DAO's `create_update_booking()` does upsert by `booking_id`
6. Customer data synced, Klaviyo notified for new customers

### Three Booking Types (separate DB tables, same base model)
- **Booking** (`app/models/booking.py`) — regular bookings
- **Reservation** — NDIS reservations (category from `RESERVATION_CATEGORY` config)
- **SalesReservation** — sales reservations (category from `SALES_RESERVATION_CATEGORY` config)

All inherit from `BookingBase` in `app/models/base.py`, which defines all columns and hybrid properties.

### Key Patterns
- **Prices** stored as integers (cents). `dollar_string_to_int()` in `app/utils/validation.py` strips `$` and `.` from strings like `"$67.64"` → `6764`.
- **Dates** stored as UTC in DB. `app/utils/local_date_time.py` handles conversion. Multiple inbound date formats handled by `_unmangle_datetime()` in `BookingBase`.
- **Private columns** with hybrid properties: columns like `_created_at`, `_final_price` have `@hybrid_property` getters/setters that handle type coercion and timezone conversion.
- **Custom fields** mapped via config keys (`CUSTOM_SOURCE`, `CUSTOM_BOOKED_BY`, etc.) and processed in `app/models/base.py:process_custom_fields()`.
- **Team assignment** parsing: `team_details` arrives as a stringified list of dicts, parsed via `ast.literal_eval` in `get_team_list()`.
- **String truncation**: `truncate_field()` in `app/utils/validation.py` truncates and logs warnings on overflow, applied in all model `import_dict()` methods.
- **Retries**: All external HTTP calls use `tenacity` `@retry` with exponential backoff.
- **Caching**: Location lookups use `cachetools.TTLCache(maxsize=1000, ttl=3600)`.
- **HTTP client**: `httpx` for all external HTTP calls (consistent with m2m-proxy).

### File Structure
```
app/
├── main.py              # FastAPI app, lifespan, exception handlers
├── database.py          # SQLAlchemy engine, sessionmaker, get_db() dependency
├── auth.py              # verify_api_key FastAPI dependency (HTTPBearer)
├── logging_config.py    # dictConfig logging setup + Gmail error handler
├── utils/
│   ├── validation.py    # truncate_field, string_to_boolean, dollar_string_to_int, check_postcode
│   ├── email_service.py # Gmail API email sending (consolidated)
│   ├── gmail_handler.py # GmailOAuth2Handler for error emails
│   ├── klaviyo.py       # Klaviyo CRM integration (httpx + tenacity)
│   ├── local_date_time.py # Timezone utilities
│   ├── locations.py     # Location lookup (TTLCache + tenacity)
│   └── notifications.py # Webhook notifications (tenacity)
├── models/
│   ├── base.py          # BookingBase (DeclarativeBase) with all columns/hybrid properties
│   ├── booking.py       # Booking, Reservation, SalesReservation
│   ├── customer.py      # Customer
│   └── cancellation.py  # import_cancel_dict helper
├── schemas/booking.py   # Pydantic models: BookingWebhookPayload, BookingResponse, etc.
├── daos/
│   ├── base.py          # BaseDAO with mark_converted(), create_update_booking()
│   ├── booking.py       # BookingDAO (search, date range queries)
│   ├── customer.py      # CustomerDAO
│   ├── reservation.py   # ReservationDAO (thin subclass)
│   └── sales_reservation.py  # SalesReservationDAO (thin subclass)
├── routers/
│   ├── bookings.py      # /booking/* endpoints with update_table() logic
│   └── health.py        # GET / health check
├── database/            # Utility scripts (create_db, update_durations, etc.)
├── commands/            # Scheduled command scripts
└── templates/           # HTML email templates
```

### Routers
- `app/routers/bookings.py` — Booking CRUD, search, and webhook endpoints
- `app/routers/health.py` — Health check

### Database Scripts (`app/database/`)
- `create_db.py` — Initialize database tables
- `upload_booking_csv.py` — Bulk import from CSV
- `update_durations.py`, `update_locations.py`, `update_status.py` — Data backfill utilities

## Dependencies

Python 3.12, FastAPI, Uvicorn, Pydantic 2.9+, SQLAlchemy 2.0+, PostgreSQL (psycopg2), httpx, tenacity, cachetools, pendulum. Full list in `requirements.txt`.

## Deployment

Heroku-based. `Procfile` runs `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Database via `DATABASE_URL` env var (auto-corrects `postgres://` to `postgresql://` prefix).
