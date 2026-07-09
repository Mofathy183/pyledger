"""Application configuration models and settings loaders.

Defines the configuration surface used during application startup and
provides isolated settings models for production and test environments.
Configuration is loaded from environment variables and optional dotenv
files through Pydantic Settings.
"""

from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoSettings(BaseModel):
    """MongoDB connection settings.

    Groups the connection details required to access the application's
    MongoDB database. Nested under the root Settings model so related
    database configuration remains together.
    """

    uri: str = Field(
        default="mongodb://localhost:27017",
        description="The URI of the MongoDB database.",
    )
    db: str = Field(
        default="pyledger",
        description="The name of the MongoDB database.",
    )

    server_selection_timeout_ms: int = Field(
        default=5000,
        description="Maximum time in milliseconds to wait for MongoDB server selection.",
    )
    min_pool_size: int = Field(
        default=1,
        description="Minimum number of connections maintained in the MongoDB connection pool.",
    )
    retry_reads: bool = Field(
        default=True,
        description="Whether retryable reads are enabled.",
    )
    retry_writes: bool = Field(
        default=True,
        description="Whether retryable writes are enabled.",
    )


class ApiSettings(BaseModel):
    """API-layer configuration, independent of Mongo/domain settings."""

    title: str = Field(
        default="PyLedger API",
        description="Title displayed in the OpenAPI schema.",
    )
    version: str = Field(
        default="0.1.0",
        description="Current API version.",
    )
    description: str = Field(
        default="REST API for the PyLedger accounting engine.",
        description="Description displayed in the OpenAPI schema.",
    )

    host: str = Field(
        default="127.0.0.1",
        description="Host interface the API server binds to.",
    )
    port: int = Field(
        default=8000,
        description="Port the API server listens on.",
    )
    reload: bool = Field(
        default=False,
        description="Enable uvicorn's auto-reload. Intended for local development only.",
    )


class Settings(BaseSettings):
    """Root application configuration.

    Loads application settings from the environment using the
    ``PYLEDGER_`` namespace and exposes strongly typed configuration
    objects to the rest of the application.
    """

    model_config = SettingsConfigDict(
        env_prefix="PYLEDGER_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    mongo: MongoSettings = Field(default_factory=MongoSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)


class TestSettings(Settings):
    """Configuration isolated from production settings.

    Inherits the application configuration structure but loads values
    from a separate environment-variable namespace and dotenv file.
    This prevents test runs from unintentionally consuming production
    configuration.
    """

    model_config = SettingsConfigDict(
        env_prefix="PYLEDGER_TEST_",
        env_file=".env.test",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance.

    Settings are loaded once and reused for the lifetime of the process
    so callers receive a consistent configuration view without repeatedly
    re-reading environment sources.

    Returns:
        The application settings instance.
    """
    return Settings()
