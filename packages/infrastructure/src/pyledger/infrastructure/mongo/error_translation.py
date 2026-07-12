"""MongoDB exception translation utilities.

Provides the translate_mongo_errors() async context manager for use in
every repository method. Translates PyMongo exceptions into AppError at
the repository boundary so that the service layer never handles
driver-specific exceptions.

DuplicateKeyError is intentionally excluded — callers that need to
differentiate code vs name_key violations must catch it before entering
this context. See MongoAccountRepo._on_duplicate() for the pattern.

Exception hierarchy (most-specific first):
    ServerSelectionTimeoutError
        └─ subclass of ConnectionFailure
        └─ maps to AppError.storage_timeout()
    ConnectionFailure
        └─ maps to AppError.storage_unavailable()
    PyMongoError  (catch-all; DuplicateKeyError is a subclass, so callers
                    MUST catch DuplicateKeyError BEFORE entering this context
                    when they write data — otherwise it collapses to unknown)
        └─ maps to AppError.unknown()
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from beanie.exceptions import DocumentNotFound
from pyledger.shared.errors import AppError
from pymongo.errors import (
    ConnectionFailure,
    DuplicateKeyError,
    PyMongoError,
    ServerSelectionTimeoutError,
)


def violated_index(exc: DuplicateKeyError) -> str | None:
    """Return the first field name from the violated index, or None."""
    key_pattern = (exc.details or {}).get("keyPattern", {})
    return next(iter(key_pattern), None)


@asynccontextmanager
async def translate_mongo_errors() -> AsyncGenerator[None]:
    """Translate PyMongo infrastructure exceptions into AppError.

    Wraps a single awaitable Beanie call so that storage-level failures
    never escape the repository boundary as driver-specific exceptions.

    Usage — read path (no DuplicateKeyError risk):

        async with translate_mongo_errors():
            doc = await AccountDocument.find_one(...)

    Usage — write path (DuplicateKeyError must be caught first):

        try:
            async with translate_mongo_errors():
                await doc.insert()
        except DuplicateKeyError as exc:
            raise self._on_duplicate(exc, account) from exc

    DuplicateKeyError is a PyMongoError subclass. If a write method
    enters this context without the outer DuplicateKeyError catch, a
    unique-index violation silently becomes AppError.unknown(). The unit
    test for this context manager explicitly asserts that DuplicateKeyError
    propagates through uncaught.

    Raises:
        AppError: STORAGE_TIMEOUT when ServerSelectionTimeoutError is caught.
        AppError: STORAGE_UNAVAILABLE when ConnectionFailure is caught.
        AppError: UNKNOWN_ERROR for any other PyMongoError.
    """
    try:
        yield
    except DuplicateKeyError:
        raise  # repository handles this — it knows what the indexes mean
    except DocumentNotFound:
        raise  # repository handles this — it knows which resource is missing
    except ServerSelectionTimeoutError as exc:
        raise AppError.storage_timeout(cause=exc) from exc
    except ConnectionFailure as exc:
        raise AppError.storage_unavailable(cause=exc) from exc
    except PyMongoError as exc:
        raise AppError.unknown(cause=exc) from exc
