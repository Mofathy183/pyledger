# pyledger-infrastructure

The concrete MongoDB/Beanie storage adapters for PyLedger. This package is the
only place in the workspace where `beanie` and `pymongo` are imported.

## What is this package?

`pyledger-infrastructure` implements the repository contracts defined in
`pyledger-core` (`AccountRepo`, `JournalRepo`, `PostingRepo`) against a real
MongoDB database, and provides the connection lifecycle and error-translation
utilities every one of those adapters relies on.

## Why does it exist?

`pyledger-core` defines its repository contracts as storage-agnostic ABCs —
they know nothing about MongoDB, Beanie, or PyMongo. Something in the
workspace has to actually talk to a database. That's this package. Keeping it
separate means the accounting domain (`pyledger-core`) stays swappable to a
different storage backend later without changing a single service or domain
model.

## Responsibilities

- Open and close a verified MongoDB connection (`connect()`, `disconnect()`,
  `MongoConnection`).
- Translate MongoDB/PyMongo/Beanie exceptions into `AppError` before they
  cross the repository boundary (`translate_mongo_errors()`,
  `violated_index()`, `MongoExecutor`).
- Provide a shared base document with automatic `created_at`/`updated_at`
  management (`TimestampedDocument`).
- Provide concrete Beanie documents + repository implementations for each
  bounded context: `account`, `journal`, `posting`.

This package does **not** contain accounting rules, business validation, or
uniqueness pre-checks — those belong to `pyledger-core`'s services and domain
schemas. It also does not import `typer`, `rich`, or `fastapi`.

## Public API

```txt
pyledger.infrastructure.mongo            -> MongoConnection, connect, disconnect
pyledger.infrastructure.mongo.shared     -> TimestampedDocument, MongoExecutor
pyledger.infrastructure.mongo.account    -> AccountDocument, MongoAccountRepo
pyledger.infrastructure.mongo.journal    -> JournalDocument, JournalLineSubDocument, MongoJournalRepo
pyledger.infrastructure.mongo.posting    -> PostingDocument, MongoPostingRepo
```

`error_translation.py` (`translate_mongo_errors`, `violated_index`) is used
internally by every repository and by `MongoExecutor`; it is not re-exported
from a package `__init__.py` today, so import it from
`pyledger.infrastructure.mongo.error_translation` directly if you need it.

## Installation

From the workspace root:

```bash
uv sync --package pyledger-infrastructure
```

or `uv sync` to install the whole workspace.

## Usage

### Opening a connection

```python
from pyledger.config import get_settings
from pyledger.infrastructure.mongo import connect, disconnect

settings = get_settings()
connection = await connect(settings.mongo)   # verifies connectivity with a ping
...
await disconnect(connection)
```

### Wiring a repository

Every concrete repository takes a `MongoExecutor`, not a raw client or
database handle:

```python
from beanie import init_beanie
from pyledger.infrastructure.mongo import connect
from pyledger.infrastructure.mongo.account import AccountDocument, MongoAccountRepo
from pyledger.infrastructure.mongo.journal import JournalDocument
from pyledger.infrastructure.mongo.posting import PostingDocument
from pyledger.infrastructure.mongo.shared import MongoExecutor

connection = await connect(settings.mongo)
await init_beanie(
    database=connection.db,
    document_models=[AccountDocument, JournalDocument, PostingDocument],
)

executor = MongoExecutor()
account_repo = MongoAccountRepo(executor)
```

`init_beanie()` must run before any repository is constructed — every
repository's docstring states this as a precondition. Forgetting it raises
`CollectionWasNotInitialized` the first time the repository touches Mongo.

### Using a repository

Repositories are consumed through the `AccountRepo`/`JournalRepo`/
`PostingRepo` contracts from `pyledger-core`, so calling code never needs to
import the concrete `Mongo*Repo` classes directly except at composition time:

```python
account = await account_repo.get_by_code("1001")
```

## Integration with the rest of the repo

- **Consumers:** `apps/cli` and `apps/api` each construct these repositories
  in their own composition root (`CliContext`, the API's `bootstrap.py`), then
  hand them to `pyledger-core` services.
- **Never a consumer of:** `pyledger-cli` or `pyledger-api` — this package
  never imports an app, and an import-linter contract in the root
  `pyproject.toml` fails the build if it ever does.
- **Depends on:** `pyledger-shared` (errors, rules), `pyledger-core`
  (repository contracts, domain schemas), `pyledger-config` (`MongoSettings`),
  `beanie`, `pymongo`.

## Extending — adding a new bounded-context adapter

Follow the shape already established by `account`/`journal`/`posting`:

1. Add `mongo/<feature>/document.py` — a `TimestampedDocument` subclass (or
   `pydantic.BaseModel` for embedded subdocuments) with a `Settings` class
   declaring the collection name and indexes.
2. Add `mongo/<feature>/repository.py` — a `Mongo<Feature>Repo` implementing
   the corresponding `pyledger-core` repo contract, built around a single
   `_to_document()`/`_to_domain()` mapping boundary and a `MongoExecutor`.
3. Add `mongo/<feature>/__init__.py` re-exporting the document(s) and repo.
4. Register the new `Document` class wherever `init_beanie()` is called in
   production, and add it to `tests/fixtures/mongo.py::DOCUMENT_MODELS` so
   integration tests pick it up.
5. Add `mongo/<feature>/tests/test_document.py`,
   `test_repository_unit.py` (pure mapping logic, no I/O), and
   `test_repository_integration.py` (real MongoDB, `@pytest.mark.integration`).

## Testing

- **Unit tests** live beside each adapter under `mongo/<feature>/tests/` and
  never touch a real database. Document construction is exercised via
  `Document.model_construct(...)` or a `stub_*_document_settings` fixture
  that patches `get_settings()` so `Document.__init__` doesn't require
  `init_beanie()` to have run.
- **Integration tests** (`test_repository_integration.py`, marked
  `@pytest.mark.integration`) run against a real MongoDB instance via the
  `mongo_connection` → `beanie_init` → `clean_db` → `mongo_<feature>_repo`
  fixture chain in `tests/fixtures/`. `clean_db` truncates collections
  between tests rather than dropping them, so indexes survive the whole
  session.
- Run just this package's tests with `pytest -m "unit and infra"` /
  `pytest -m "integration and infra"` (see the root `conftest.py`, which
  derives the `infra` marker automatically from file path).

## Known limitations

- `MongoPostingRepo.save_many()` writes its batch with a single
  `insert_many()` and no `ClientSession` — there is no multi-document
  transaction support anywhere in this package today. A mid-batch
  interruption can partially persist a journal's postings, and two
  concurrent posting attempts for the same journal number can both pass
  `PostingService`'s pre-check before either writes.
- There is no second storage backend yet (e.g. Postgres) — every repository
  contract currently has exactly one concrete implementation, this one.
