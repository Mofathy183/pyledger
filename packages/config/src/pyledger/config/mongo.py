"""Application configuration models and settings loaders.

Defines the configuration surface used during application startup and
provides isolated settings models for production and test environments.
Configuration is loaded from environment variables and optional dotenv
files through Pydantic Settings.
"""

from pydantic import BaseModel, Field


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
