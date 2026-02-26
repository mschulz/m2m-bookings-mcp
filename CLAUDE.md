# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI server that collects booking and customer data via Zapier webhooks, communicating with m2m-proxy (a FastAPI proxy at `../m2m-proxy`) instead of Launch27 directly. It stores data in PostgreSQL and integrates with Gmail, Klaviyo, and Zapier for notifications and CRM.

## Running the Application

```bash
python run.py
```

Production uses Uvicorn: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Configuration

- Uses `pydantic_settings.BaseSettings` in `app/core/config.py` with `.env` file
- `ENVIRONMENT` field (development/staging/production/testing) controls behavior
- Computed properties: `debug`, `testing`, `log_to_stdout` derived from `ENVIRONMENT`
- `testing=True` suppresses email sending
- API authentication via Bearer token in Authorization header, validated against `API_KEY`
- Proxy config: `PROXY_URL`, `PROXY_API_KEY`
- `KLAVIYO_ENABLED` (default `true`): set `false` to disable Klaviyo new-customer notifications
- Settings singleton via `@lru_cache` on `get_settings()`

## Architecture

**Fully async/await.** Routes, services, DAOs, and HTTP clients all use `async def` with `await`. The DB driver is `asyncpg` via `create_async_engine` and `AsyncSession`.

**DAO Pattern:** Routes stay thin, calling DAO methods directly. DAOs are module-level singletons. All DAO methods are async and accept a `db: AsyncSession` parameter injected via FastAPI's `Depends(get_db)`.

### Request Flow (webhook from Zapier)
1. POST hits route (e.g., `/booking/new`)
2. `verify_api_key` FastAPI dependency validates Bearer token
3. FastAPI exception handlers catch DB connection drops (503) and data errors (422)
4. Route parses JSON body, calls `await update_table()` which calls the booking DAO
5. DAO's `create_update_booking()` does upsert via `Model.from_webhook(data)` (create) or `instance.update_from_webhook(data)` (update), then resolves location via async `_resolve_location()`
6. Customer data synced, Klaviyo notified for new customers

### SQLModel (unified ORM + Pydantic)
Models use **SQLModel** — one class defines both the DB table and Pydantic validation. This replaces the previous separate SQLAlchemy models + Pydantic schemas.

- `BookingBase(SQLModel)` in `app/models/base.py` defines all shared columns
- `Booking` inherits from `BookingBase` with `table=True` (single table for all booking types)
- DB column names with underscore prefixes (`_created_at`, `_final_price`) are mapped using `sa_column_kwargs={"name": "_created_at"}` so Python uses clean names (`created_at`, `final_price`)
- `model_dump(mode="json")` replaces the old `to_json()` method
- Webhook data import uses `from_webhook()` / `update_from_webhook()` classmethods with explicit coercion via standalone parsing functions

### Key Patterns
- **Prices** stored as integers (cents). `dollar_string_to_int()` in `app/utils/validation.py` strips `$` and `.` from strings like `"$67.64"` → `6764`.
- **Dates** stored as UTC in DB. `app/utils/local_date_time.py` handles conversion. Multiple inbound date formats handled by `parse_datetime()` and `parse_date()` in `app/utils/validation.py`.
- **Column name mapping**: DB columns like `_created_at` are accessed as `created_at` in Python via `sa_column_kwargs={"name": "..."}`. API responses use clean names.
- **Custom fields** mapped via config keys (`CUSTOM_SOURCE`, `CUSTOM_BOOKED_BY`, etc.) and processed in `app/models/base.py:process_custom_fields()`.
- **Team assignment** parsing: `team_details` arrives as a stringified list of dicts, parsed via `parse_team_list()` in `app/utils/validation.py`.
- **String truncation**: `truncate_field()` in `app/utils/validation.py` truncates and logs warnings on overflow, applied in webhook import methods.
- **Retries**: All external HTTP calls use `tenacity` `@retry` with exponential backoff.
- **Caching**: Location lookups use `cachetools.TTLCache(maxsize=1000, ttl=3600)`.
- **HTTP client**: `httpx.AsyncClient` for all external HTTP calls (consistent with m2m-proxy).
- **Location resolution**: Models (`from_webhook`/`update_from_webhook`) only set `location` if provided in webhook data. The DAO layer resolves missing locations via async `_resolve_location()` → `get_location()` after applying webhook data.
- **Sync Google API**: `email_service.py` and `gmail_handler.py` remain sync; called via `run_in_threadpool()` from the async exception handler.

### File Structure
```
app/
├── main.py              # FastAPI app, MCP mount, lifespan, exception handlers
├── core/
│   ├── config.py        # pydantic_settings.BaseSettings, get_settings()
│   ├── auth.py          # verify_api_key FastAPI dependency (HTTPBearer)
│   ├── database.py      # AsyncSession engine, async_sessionmaker, get_db() dependency
│   └── logging_config.py # dictConfig logging setup + Gmail error handler
├── utils/
│   ├── validation.py    # Parsing (parse_datetime, parse_date, parse_team_list, etc.) + truncation + coercion
│   ├── email_service.py # Gmail API email sending (consolidated)
│   ├── gmail_handler.py # GmailOAuth2Handler for error emails
│   ├── klaviyo.py       # Klaviyo CRM integration (async httpx + tenacity)
│   ├── local_date_time.py # Timezone utilities
│   └── locations.py     # Location lookup (async httpx, TTLCache + tenacity)
├── models/
│   ├── base.py          # BookingBase(SQLModel) with all columns + from_webhook/update_from_webhook
│   ├── booking.py       # Booking model (single table for all booking types)
│   ├── customer.py      # Customer(SQLModel, table=True)
│   └── cancellation.py  # apply_cancellation_data helper
├── schemas/booking.py   # Pydantic response models: BookingResponse, BookingSearchResult
├── daos/
│   ├── base.py          # BaseDAO with create_update_booking(), _resolve_location()
│   ├── booking.py       # BookingDAO (search, date range queries)
│   └── customer.py      # CustomerDAO
├── services/
│   ├── bookings.py      # Booking business logic (update_table, search helpers)
│   └── customers.py     # Customer business logic (create_or_update_customer)
├── routers/
│   ├── bookings.py      # /booking/* endpoints (thin routes)
│   ├── customers.py     # /customer/* endpoints (thin routes)
│   └── health.py        # GET / health check
├── commands/            # Scheduled command scripts
└── templates/           # HTML email templates
scripts/
└── copy_old_db.py       # One-time migration: copy data from old DB to new DB
```

### Routers
- `app/routers/bookings.py` — Booking CRUD, search, and webhook endpoints
- `app/routers/customers.py` — Customer webhook endpoints
- `app/routers/health.py` — Health check

## Dependencies

Python 3.12, FastAPI, Uvicorn, SQLModel 0.0.22+, Pydantic 2.9+, SQLAlchemy 2.0+, PostgreSQL (asyncpg + psycopg2-binary for scripts), greenlet, httpx, tenacity, cachetools, pendulum, fastapi-mcp. Full list in `requirements.txt`.

## Deployment

Heroku-based. `Procfile` runs `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Database via `DATABASE_URL` env var (auto-corrects `postgres://` to `postgresql://` prefix, then to `postgresql+asyncpg://` at engine creation).
