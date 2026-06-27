# PyLedger

PyLedger is a Python CLI bookkeeping application built around double-entry accounting.

## Tech Stack

- Python 3.14+
- UV
- Typer
- Rich
- Pydantic v2
- Pydantic Settings
- Beanie
- PyMongo (async)
- Pytest
- Ruff
- Ty

## Repository Layout

- `src/pyledger/conftest.py` registers the shared pytest fixture plugins.
- `src/pyledger/main.py` is the console entry point.
- `src/pyledger/cli/` contains the Typer app, Rich console setup, themes, formatters, CLI constants, and the journal command scaffold.
- `src/pyledger/infrastructure/mongo/` contains the MongoDB connection helpers, shared executor and error translation,
  the MongoDB account document and repository, and MongoDB infrastructure tests.
- `src/pyledger/modules/` contains the account, journal, and posting feature packages. Account, journal, and posting each have implemented service layers.
- `src/pyledger/shared/` contains reusable validation helpers, utility functions, and the shared error model.

- `tests/` contains shared test infrastructure only: `fixtures/`, `factories/`, and `fakes/`.
- Feature tests live beside the feature code under `src/pyledger/modules/**/tests/`.
- MongoDB infrastructure tests live under `src/pyledger/infrastructure/mongo/**/tests/`.
- Shared error tests live under `src/pyledger/shared/errors/tests/`.
- There is no `src/pyledger/cli/tests/` directory today.

## Current Domain Rules

- Every journal entry must balance.
- Total debits must equal total credits.
- A journal line must contain either a debit amount or a credit amount, never both and never neither.
- Negative amounts are invalid.
- Empty account names are invalid.
- Account names are normalized by `clean_account_name()` and matched case-insensitively with `account_lookup_key()`.
- Account aliases are not implemented.
- Account categories are `Asset`, `Liability`, `Equity`, `Revenue`, `Expense`, `Dividend`, and `Drawing`.
- Normal balance is derived from the account category.
- A `JournalEntry` must contain at least two lines.
- `JournalEntry.journal_number` must be positive.
- `JournalEntry.posting_date` and `LedgerPosting.posting_date` must be later than `2020-01-01` and must not be in the future.
- `LedgerPosting` is frozen after creation.

## Current Implementation Notes

- `AccountService`, `JournalService`, and `PostingService` are the implemented feature services.
- `JournalService` exposes `create_journal_entry()`, `get_journal_entry()`, and `list_journal_entries()`, plus private mapping helpers.
- `JournalService._to_entry_view()` is a normal instance method, not a broken staticmethod.
- `JournalRepo` defines `save()`, `get_by_number()`, `list_entries()`, and `next_journal_number()`.
- `PostingService` exposes `post_journal_entry()`, `get_postings_by_account()`, and `get_postings_by_journal_number()`.
- `pyledger.infrastructure.mongo` exposes `MongoConnection`, `connect()`, and `disconnect()`.
- `pyledger.infrastructure.mongo.shared` exposes `TimestampedDocument`, `MongoExecutor`, and the Mongo error translator.
- `pyledger.infrastructure.mongo.account` exposes `AccountDocument` and `MongoAccountRepo`.
- `cli/formatters/error_fmt.py` and `cli/constants/errors.py` exist and import, but no CLI command currently wires them into a user-facing workflow.
- `modules/journal/repo.py` is an implemented async repository contract.
- `modules/journal/rule.py` remains an empty scaffold.
- `modules/posting/dtos.py` defines `PostingViewModel`. `modules/posting/rule.py` remains an empty scaffold.
- `modules/journal/__init__.py` re-exports the journal repo, service, and DTOs.
- `modules/posting/__init__.py` re-exports `PostingRepo`, `PostingService`, and `PostingViewModel`.
- `main.py` is a thin console entry point that only invokes `app()`.
- `cli/constants/errors.py` still has wording drift for invalid account names and unknown accounts; its copy mentions abbreviations and aliases even though alias support is not implemented and `clean_account_name()` does not allow commas.
- `CreateJournalInput` omits `journal_number`; `JournalService` assigns it via `JournalRepo.next_journal_number()`.
- `PostingService` is implemented and available for journal-to-posting workflows, though it is not yet wired into the CLI.

## Development Rules

- Keep business logic independent of Typer and Rich.
- Keep domain validation inside the feature modules.
- Use Pydantic models for domain validation and DTOs for service boundaries.
- Prefer composition to inheritance.
- Use strict typing.
- Keep CLI code thin and presentation-only.
- Keep repository contracts async when they are meant to sit behind storage adapters.
- Do not document alias support, chart resolution helpers, or service methods as implemented unless the code actually provides them.

## Tooling

- Use `ruff format` and `ruff check` for formatting and linting.
- Use `ty check` for static type checking.
- Use `pytest` for tests.
- The pytest configuration sets `-ra`, strict markers, importlib mode, and session-scoped asyncio loop defaults. Run
  `pytest -m unit` for the fast suite and `pytest -m integration` for Mongo-backed tests. If Windows file locking
  interferes with local runs, `pytest -o addopts=""` is the quickest way to inspect the raw test results.

## Configuration and Infrastructure

- `pyledger.config` exposes `Settings`, `TestSettings`, `MongoSettings`, and `get_settings()`.
- Settings load from environment variables under the `PYLEDGER_` prefix and an optional `.env` file.
- `TestSettings` uses the `PYLEDGER_TEST_` prefix and `.env.test` to keep test configuration isolated from production.
- Nested settings use `PYLEDGER_*__*` environment variables such as `PYLEDGER_TEST_MONGO__URI`.
- `get_settings()` is cached with `lru_cache`; tests must call `get_settings.cache_clear()` before and after mutating the environment.
- `pyledger.infrastructure.mongo` provides `connect()`, `disconnect()`, and the `MongoConnection` dataclass for MongoDB lifecycle management.
- `pyledger.infrastructure.mongo.shared` provides `MongoExecutor`, `TimestampedDocument`, and error translation helpers.
- `pyledger.infrastructure.mongo.account` provides the concrete MongoDB account repository.
- Do not couple domain models, services, or CLI code to `MongoSettings`, `AsyncMongoClient`, `MongoExecutor`, or any infrastructure type.

## Testing Guidance

- Domain tests live beside the feature code under `src/pyledger/modules/**/tests/`.
- Shared error tests live under `src/pyledger/shared/errors/tests/`.
- Shared rule tests live under `src/pyledger/shared/tests/`.
- Shared fixtures, factories, and fakes live under `tests/`. `tests/factories/posting.py` and `tests/fakes/posting_repo.py` support posting service tests.
- Current automated coverage is concentrated on domain models, shared validation helpers, shared error translation, `AccountService`, `JournalService`, `PostingService`, and MongoDB infrastructure behavior.
- Journal schema tests cover `JournalLine` and `JournalEntry` validation.
- Journal DTO tests cover the journal input and view models.
- Journal service tests cover create, get, list, account validation, domain validation, and journal-number allocation workflows.
- Posting schema tests cover `LedgerPosting` validation.
- Posting DTO tests cover `PostingViewModel`.
- Posting service tests cover journal-to-posting derivation, duplicate-posting prevention, and posting retrieval workflows.
- MongoDB connection tests live under `src/pyledger/infrastructure/mongo/tests/`.
- MongoDB account repository tests live under `src/pyledger/infrastructure/mongo/account/tests/`.
- There are no journal or posting storage adapter tests, reporting tests, or user-facing CLI workflow tests yet.
- Settings tests live under `src/pyledger/config/tests/`.
- `tests/fixtures/settings.py` provides a session-scoped `test_settings` fixture backed by `TestSettings` and the
  `isolate_settings_cache` autouse fixture that clears `get_settings.cache_clear()` before and after every test.
- `tests/fixtures/mongo.py` provides `mongo_connection`, `beanie_init`, and `clean_db` fixtures for Mongo-backed integration tests.
- `src/pyledger/conftest.py` registers all fixture modules.

## Error Handling

- `pyledger.shared.errors` is the shared error boundary.
- `ErrorCode`, `AppError`, `ValidationAppError`, and `FieldViolation` are the stable public error types.
- Pydantic validation is translated through `pydantic_error()` and `get_field_violations()`.
- `AppError.storage_unavailable()` and `AppError.storage_timeout()` are the storage-specific error constructors.
- CLI wording belongs in the CLI layer, not in shared errors.
- Keep `AppError` as the only exception type that should cross a service boundary.
- Reconcile `cli/constants/errors.py` and `cli/formatters/error_fmt.py` with the shared error model before relying on them in new code.

## Service And Repository Boundaries

- `AccountRepo`, `JournalRepo`, and `PostingRepo` are the repository contracts.
- `MongoAccountRepo` is the concrete MongoDB account repository implementation.
- There is no concrete journal or posting repository implementation in the repository today.
- Service methods that talk to repos remain async.
- Services should orchestrate domain objects and repositories, not render terminal output.
- CLI code should consume DTOs or view models, not repository implementations or domain internals.
