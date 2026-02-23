# app/main.py

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import exc

from app.logging_config import setup_logging
from app.database import engine, Base
from app.routers import bookings, health
from config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    settings = get_settings()
    logger.info("%s: starting ...", settings.APP_NAME)

    # Ensure tables exist (optional - usually handled by migrations)
    Base.metadata.create_all(bind=engine)

    yield

    # Shutdown
    engine.dispose()
    logger.info("%s: shutting down ...", settings.APP_NAME)


app = FastAPI(
    title="M2M Bookings",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(health.router)
app.include_router(bookings.router)

# Mount MCP server
from fastapi_mcp import FastApiMCP

mcp = FastApiMCP(
    app,
    name="M2M Bookings MCP",
    description="M2M Bookings database - query and manage cleaning bookings, customers, and reservations",
)
mcp.mount_http()


# --- Exception Handlers ---


@app.exception_handler(exc.OperationalError)
async def sqlalchemy_operational_error_handler(request: Request, e: exc.OperationalError):
    logger.error("Database operational error: %s", e)
    return JSONResponse(
        status_code=503,
        content={"error": "Database temporarily unavailable", "status_code": 503},
    )


@app.exception_handler(exc.DataError)
async def sqlalchemy_data_error_handler(request: Request, e: exc.DataError):
    logger.error("Database data error: %s", e)
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid data", "status_code": 422},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, e: Exception):
    logger.error("Unhandled exception on %s: %s", request.url.path, e, exc_info=True)

    settings = get_settings()
    if not settings.testing:
        try:
            from app.services.email_service import send_error_email
            m = settings.SUPPORT_EMAIL.split("@")
            to_addr = f"{m[0]}+error@{m[1]}"
            send_error_email(to_addr, f"({request.url.path}) {str(e)}")
        except Exception as email_err:
            logger.error("Failed to send error email: %s", email_err)

    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500},
    )
