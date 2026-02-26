"""Application settings loaded from environment variables and .env file."""

from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field


class Environment(str, Enum):
    development = "development"
    staging = "staging"
    production = "production"
    testing = "testing"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: Environment = Environment.development

    # API Authentication
    API_KEY: str = ""
    SECRET_KEY: str = "you-will-never-guess"

    # Company and app data
    COMPANY_NAME: str = ""
    COMPANY_URL: str = ""
    APP_NAME: str = ""
    PHONE: str = ""
    RATING_SERVER: str = ""

    # Timezone information
    TZ_LOCALTIME: str = "Australia/Brisbane"
    TZ_ISDST: str | None = None

    # Database configuration
    DATABASE_URL: str = "postgresql:///test"

    # Proxy (was Launch27)
    PROXY_URL: str = ""
    PROXY_API_KEY: str = ""

    # Email settings
    FROM_NAME: str = ""
    FROM_ADDRESS: str = ""
    SUPPORT_EMAIL: str = ""
    OVERRIDE_EMAIL: bool = True
    OVERRIDE_ADDR: str = ""

    # Gmail OAuth service account credentials (JSON string)
    SERVICE_ACCOUNT_CREDENTIALS: str = ""
    GMAIL_SERVICE_ACCOUNT_CREDENTIALS: str = ""

    # Custom fields
    CUSTOM_SOURCE: str | None = None
    CUSTOM_BOOKED_BY: str | None = None
    CUSTOM_EMAIL_INVOICE: str | None = None
    CUSTOM_INVOICE_NAME: str | None = None
    CUSTOM_WHO_PAYS: str | None = None
    CUSTOM_INVOICE_EMAIL_ADDRESS: str | None = None
    CUSTOM_LAST_SERVICE: str | None = None
    CUSTOM_INVOICE_REFERENCE: str | None = None
    CUSTOM_INVOICE_REFERENCE_EXTRA: str | None = None
    CUSTOM_NDIS_NUMBER: str | None = None
    CUSTOM_FLEXIBLE: str | None = None
    CUSTOM_HOURLY_NOTES: str | None = None

    # Booking type categories
    SERVICE_CATEGORY_DEFAULT: str = "House Clean"

    # Klaviyo
    KLAVIYO_ENABLED: bool = True
    MY_KLAVIYO_URL: str = ""
    MY_KLAVIYO_API_KEY: str = ""

    # zip2location URL
    ZIP2LOCATION_URL: str = ""

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return self.DATABASE_URL.replace("postgres://", "postgresql://")

    @computed_field
    @property
    def debug(self) -> bool:
        return self.ENVIRONMENT in (Environment.development, Environment.staging, Environment.testing)

    @computed_field
    @property
    def testing(self) -> bool:
        return self.ENVIRONMENT == Environment.testing

    @computed_field
    @property
    def log_to_stdout(self) -> bool:
        return True


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()
