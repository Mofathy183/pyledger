# Trutina

Trutina is a Python CLI bookkeeping application built around double-entry accounting.

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

- `src/trutina/conftest.py` registers the shared pytest fixture plugins.
- `src/trutina/main.py` is the console entry point. It builds the production `CliContext` via `bootstrap.build_context()` and calls `run()`, which opens the CLI's single `BlockingPortal`, constructs `CliState`, and dispatches the Typer app, guaranteeing `context.aclose()` runs in a `finally` block regardless of outcome.
- `src/trutina/cli/` contains the Typer app (`app.py`), the composition root (`bootstrap.py`), the per-invocation dependency container (`context.py`), the sync-to-async bridge (`state.py`), and the feature-oriented command packages under `cli/features/`.
- `src/trutina/cli/features/{account,journal,posting}/` each contain `command.py` (Typer command group), `parser.py` (CLI-flag input → DTO), `prompt.py` (interactive input → DTO), `handler.py` (DTO → service call), `formatter.py` (ViewModel → Rich renderable), and `tests/`.
- `src/trutina/cli/shared/` contains the error boundary (`error_boundary.py`), generic interactive prompt primitives (`interaction/`), the shared themed Rich console and widget factories (`ui/`), the CLI-owned error message/hint catalogs (`errors/`), and Pydantic/AppError-to-panel formatting (`formatters/`).
- `src/trutina/infrastructure/mongo/` contains the MongoDB connection helpers, shared executor and error translation, the MongoDB account, journal, and posting documents and repositories, and MongoDB infrastructure tests.
- `src/trutina/modules/` contains the account, journal, and posting feature packages. Account, journal, and posting each have implemented service layers.
- `src/trutina/shared/` contains reusable validation helpers, utility functions, and the shared error model.

- `tests/` contains shared test infrastructure only: `fixtures/`, `factories/`, and `fakes/`.
- Feature tests live beside the feature code under `src/trutina/modules/**/tests/`.
- CLI feature tests live beside the CLI feature code under `src/trutina/cli/features/**/tests/`, split into fake-backed unit tests and MongoDB-backed integration tests.
- CLI composition-root tests (`CliContext`, `CliState`, `bootstrap.build_context()`, `app.py`) live under `src/trutina/cli/tests/`.
- MongoDB infrastructure tests live under `src/trutina/infrastructure/mongo/**/tests/`.
- Shared error tests live under `src/trutina/shared/errors/tests/`.
- `src/trutina/cli/tests/` now exists and contains CliContext, CliState, bootstrap, and app-level tests, per the completed CLI README.

For full CLI architecture, layering rules, and extension guidance, see `src/trutina/cli/README.md` — this file only summarizes CLI-related facts relevant to cross-cutting repository conventions.

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
- `MongoJournalRepo` implements the journal repository contract against MongoDB and maps duplicate journal-number
  collisions to `ErrorCode.DUPLICATE_JOURNAL_NUMBER`.
- `trutina.infrastructure.mongo.posting` exposes `PostingDocument` and `MongoPostingRepo`.
- `PostingService` exposes `post_journal_entry()`, `get_postings_by_account()`, and `get_postings_by_journal_number()`.
- `trutina.infrastructure.mongo` exposes `MongoConnection`, `connect()`, and `disconnect()`.
- `trutina.infrastructure.mongo.shared` exposes `TimestampedDocument`, `MongoExecutor`, and the Mongo error translator.
- `trutina.infrastructure.mongo.account` exposes `AccountDocument` and `MongoAccountRepo`.
- `trutina.infrastructure.mongo.journal` exposes `JournalDocument`, `JournalLineSubDocument`, and `MongoJournalRepo`.
- `cli/shared/formatters/error.py` and `cli/shared/errors/{errors,hint}.py` are fully wired into every CLI command via `cli/shared/error_boundary`.py, which every command uses to catch `AppError/ValidationAppError/pydantic.ValidationError` and render them as Rich panels with a typer.Exit(code=1).
- `modules/journal/repo.py` is an implemented async repository contract.
- `infrastructure/mongo/journal/` contains the concrete MongoDB journal repository implementation.
- `infrastructure/mongo/posting/` contains the concrete MongoDB posting repository implementation.
- `modules/journal/rule.py` remains an empty scaffold.
- `modules/posting/dtos.py` defines `PostingViewModel`. `modules/posting/rule.py` remains an empty scaffold.
- `modules/journal/__init__.py` re-exports the journal repo, service, and DTOs.
- `modules/posting/__init__.py` re-exports `PostingRepo`, `PostingService`, and `PostingViewModel`.
- `main.py` is a thin console entry point. `main()` builds the production CliContext via `bootstrap.build_context()` and calls `run()`, which owns the CLI's single BlockingPortal for the life of the process and guarantees `context.aclose()` runs on exit.
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

- `trutina.config` exposes `Settings`, `TestSettings`, `MongoSettings`, and `get_settings()`.
- Settings load from environment variables under the `TRUTINA_` prefix and an optional `.env` file.
- `TestSettings` uses the `TRUTINA_TEST_` prefix and `.env.test` to keep test configuration isolated from production.
- Nested settings use `TRUTINA_*__*` environment variables such as `TRUTINA_TEST_MONGO__URI`.
- `get_settings()` is cached with `lru_cache`; tests must call `get_settings.cache_clear()` before and after mutating the environment.
- `trutina.infrastructure.mongo` provides `connect()`, `disconnect()`, and the `MongoConnection` dataclass for MongoDB lifecycle management.
- `trutina.infrastructure.mongo.shared` provides `MongoExecutor`, `TimestampedDocument`, and error translation helpers.
- `trutina.infrastructure.mongo.account` provides the concrete MongoDB account repository.
- `trutina.infrastructure.mongo.journal` provides the concrete MongoDB journal repository.
- Do not couple domain models, services, or CLI code to `MongoSettings`, `AsyncMongoClient`, `MongoExecutor`, or any infrastructure type.

## Testing Guidance

- Domain tests live beside the feature code under `src/trutina/modules/**/tests/`.
- Shared error tests live under `src/trutina/shared/errors/tests/`.
- Shared rule tests live under `src/trutina/shared/tests/`.
- Shared fixtures, factories, and fakes live under `tests/`. `tests/fixtures/journal.py`, `tests/fixtures/mongo.py`,
  and `tests/fixtures/posting.py` provide journal, MongoDB, and posting fixtures, while `tests/factories/posting.py`
  and `tests/fakes/posting_repo.py` support posting service tests.
- Current automated coverage is concentrated on domain models, shared validation helpers, shared error translation, `AccountService`, `JournalService`, `PostingService`, and MongoDB infrastructure behavior.
- Journal schema tests cover `JournalLine` and `JournalEntry` validation.
- Journal DTO tests cover the journal input and view models.
- Journal service tests cover create, get, list, account validation, domain validation, and journal-number allocation workflows.
- Posting schema tests cover `LedgerPosting` validation.
- Posting DTO tests cover `PostingViewModel`.
- Posting service tests cover journal-to-posting derivation, duplicate-posting prevention, and posting retrieval workflows.
- MongoDB posting repository tests live under `src/trutina/infrastructure/mongo/posting/tests/`.
- MongoDB connection tests live under `src/trutina/infrastructure/mongo/tests/`.
- MongoDB account repository tests live under `src/trutina/infrastructure/mongo/account/tests/`.
- MongoDB journal repository tests live under `src/trutina/infrastructure/mongo/journal/tests/`.
- CLI workflow tests exist for all three feature groups (`account`, `journal`, `posting`), split into fake-backed unit tests (`test_command_unit.py`) and MongoDB-backed integration tests (`test_command_integration.py`) under each feature's `tests/` directory, plus composition-root tests (`CliContext`, `CliState`, `build_context()`, `app.py`) under `src/trutina/cli/tests/`. There are still no reporting tests, since no reporting pipeline exists yet.
- Settings tests live under `src/trutina/config/tests/`.
- `tests/fixtures/settings.py` provides a session-scoped `test_settings` fixture backed by `TestSettings` and the
  `isolate_settings_cache` autouse fixture that clears `get_settings.cache_clear()` before and after every test.
- `tests/fixtures/journal.py` provides journal-domain fixtures, a `MongoJournalRepo` fixture, and a stub for `JournalDocument`.
- `tests/fixtures/mongo.py` provides `mongo_connection`, `beanie_init`, and `clean_db` fixtures for Mongo-backed
  integration tests. It also registers `AccountDocument`, `JournalDocument`, and `PostingDocument`, and truncates the
  collections between tests.
- `tests/fixtures/posting.py` provides `debit_posting`, `credit_posting`, `mongo_posting_repo`, and a stub for
  `PostingDocument`.
- `src/trutina/conftest.py` registers all fixture modules.

## Error Handling

- `trutina.shared.errors` is the shared error boundary.
- `ErrorCode`, `AppError`, `ValidationAppError`, and `FieldViolation` are the stable public error types.
- Pydantic validation is translated through `pydantic_error()` and `get_field_violations()`.
- `AppError.storage_unavailable()` and `AppError.storage_timeout()` are the storage-specific error constructors.
- CLI wording belongs in the CLI layer, not in shared errors.
- Keep `AppError` as the only exception type that should cross a service boundary.
- Reconcile `cli/constants/errors.py` and `cli/formatters/error_fmt.py` with the shared error model before relying on them in new code.

## Service And Repository Boundaries

- `AccountRepo`, `JournalRepo`, and `PostingRepo` are the repository contracts.
- `MongoAccountRepo` is the concrete MongoDB account repository implementation.
- `MongoJournalRepo` is the concrete MongoDB journal repository implementation.
- `MongoPostingRepo` is the concrete MongoDB posting repository implementation.
- Service methods that talk to repos remain async.
- Services should orchestrate domain objects and repositories, not render terminal output.
- CLI code should consume DTOs or view models, not repository implementations or domain internals.

## CLI Architecture

- The CLI is a feature-complete presentation layer over `AccountService`, `JournalService`, and `PostingService`, exposing `account`, `journal`, and `posting` Typer command groups.
- `cli/bootstrap.py::build_context()` is the CLI's single composition root. Constructing a `CliContext` performs no I/O — every repository and service is created lazily on first access.
- `CliContext` (`cli/context.py`) is the per-invocation dependency container: it lazily opens the shared MongoDB connection, initializes Beanie, and builds/caches repositories and services, translating connection failures to `AppError.storage_timeout()`/`AppError.storage_unavailable()`.
- `CliState` (`cli/state.py`) pairs a `CliContext` with an `anyio` `BlockingPortal` and exposes `state.call(func, *args)` as the only sanctioned bridge from a synchronous Typer command into async service/repository code.
- Each feature under `cli/features/<name>/` follows the same internal layering: `command.py` (Typer wiring) → `parser.py`/`prompt.py` (input → DTO) → `handler.py` (DTO → service call) → `formatter.py` (ViewModel → Rich renderable). Commands never call repositories or services directly, never construct domain models, and never render Rich components outside their feature's formatter.
- `cli/shared/error_boundary.py` is the single error-handling seam: it wraps one `state.call(...)` per command, catches `AppError`/`ValidationAppError`/`pydantic.ValidationError`, formats them via `cli/shared/formatters/error.py` and the CLI-owned catalogs in `cli/shared/errors/`, prints Rich panels, and raises `typer.Exit(code=1)`.
- The full CLI architecture, layer-by-layer dependency rules, async execution model, and feature-extension guide are documented in `src/trutina/cli/README.md`, which is the authoritative reference for CLI internals.
