# PyLedger Architecture

## Purpose

This document describes the current structure of PyLedger as it exists in the repository today. The codebase is
feature-oriented and is organized around account, journal, and posting modules, with separate CLI and shared support
packages.

The architectural goals are:

- keep accounting rules inside the feature modules,
- keep CLI code thin and presentation-only,
- keep reusable validation and error handling in `shared/`,
- keep persistence and reporting outside the domain models until they are implemented.

## Actual Folder Structure

```text
src/pyledger/
├── conftest.py
├── __init__.py
├── main.py
├── cli/
│   ├── __init__.py
│   ├── app.py
│   ├── bootstrap.py
│   ├── context.py
│   ├── state.py
│   ├── features/
│   │   ├── __init__.py
│   │   ├── account/
│   │   │   ├── __init__.py
│   │   │   ├── command.py
│   │   │   ├── parser.py
│   │   │   ├── prompt.py
│   │   │   ├── handler.py
│   │   │   ├── formatter.py
│   │   │   └── tests/
│   │   ├── journal/
│   │   │   ├── __init__.py
│   │   │   ├── command.py
│   │   │   ├── parser.py
│   │   │   ├── prompt.py
│   │   │   ├── handler.py
│   │   │   ├── formatter.py
│   │   │   └── tests/
│   │   └── posting/
│   │       ├── __init__.py
│   │       ├── command.py
│   │       ├── parser.py
│   │       ├── prompt.py
│   │       ├── handler.py
│   │       ├── formatter.py
│   │       └── tests/
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── error_boundary.py
│   │   ├── interaction/
│   │   │   ├── __init__.py
│   │   │   └── prompt.py
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── console.py
│   │   │   ├── widgets.py
│   │   │   └── theme/
│   │   │       ├── __init__.py
│   │   │       ├── detection.py
│   │   │       └── styles.py
│   │   ├── errors/
│   │   │   ├── __init__.py
│   │   │   ├── errors.py
│   │   │   └── hint.py
│   │   └── formatters/
│   │       ├── __init__.py
│   │       └── error.py
│   └── tests/
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── tests/
├── infrastructure/
│   ├── __init__.py
│   └── mongo/
│       ├── __init__.py
│       ├── account/
│       │   ├── __init__.py
│       │   ├── document.py
│       │   ├── repository.py
│       │   └── tests/
│       ├── connection.py
│       ├── error_translation.py
│       ├── journal/
│       │   ├── __init__.py
│       │   ├── document.py
│       │   ├── repository.py
│       │   └── tests/
│       ├── posting/
│       │   ├── __init__.py
│       │   ├── document.py
│       │   ├── repository.py
│       │   └── tests/
│       ├── shared/
│       │   ├── __init__.py
│       │   ├── document.py
│       │   ├── repository.py
│       │   └── tests/
│       └── tests/
├── modules/
│   ├── account/
│   │   ├── __init__.py
│   │   ├── dtos.py
│   │   ├── repo.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── account.py
│   │   │   └── chart.py
│   │   ├── service.py
│   │   └── tests/
│   ├── journal/
│   │   ├── __init__.py
│   │   ├── dtos.py
│   │   ├── repo.py
│   │   ├── rule.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── journal.py
│   │   │   └── line.py
│   │   ├── service.py
│   │   └── tests/
│   └── posting/
│       ├── __init__.py
│       ├── dtos.py
│       ├── repo.py
│       ├── rule.py
│       ├── schemas/
│       │   └── ledger_posting.py
│       ├── service.py
│       └── tests/
└── shared/
    ├── __init__.py
    ├── rule.py
    ├── util.py
    ├── tests/
    └── errors/
        ├── __init__.py
        ├── codes.py
        ├── errors.py
        ├── translators.py
        └── tests/
```

```text
tests/
├── fixtures/
├── factories/
└── fakes/
```

There is a `src/pyledger/conftest.py` that registers the shared fixture plugins. There is no `tests/conftest.py`
and no `tests/helpers.py`. `src/pyledger/cli/tests/` exists and holds `CliContext`, `CliState`, `bootstrap`, and
`app.py`-level tests.

## Public Exports

- `src/pyledger/modules/account/__init__.py` re-exports `AccountRepo`, `AccountService`, `CreateAccountInput`,
  `UpdateAccountInput`, `AccountViewModel`, and `ChartOfAccountsViewModel`.
- `src/pyledger/modules/journal/__init__.py` re-exports `JournalRepo`, `JournalService`, `CreateJournalInput`,
  `JournalLineInput`, `JournalLineViewModel`, and `JournalViewModel`.
- `src/pyledger/modules/posting/__init__.py` re-exports `PostingRepo`, `PostingService`, and `PostingViewModel`.
- `src/pyledger/config/__init__.py` re-exports `get_settings`, `Settings`, `TestSettings`, and `MongoSettings`.
- `src/pyledger/infrastructure/mongo/__init__.py` re-exports `MongoConnection`, `connect`, and `disconnect`.
- `src/pyledger/infrastructure/mongo/account/__init__.py` re-exports `AccountDocument` and `MongoAccountRepo`.
- `src/pyledger/infrastructure/mongo/journal/__init__.py` re-exports `JournalDocument`, `JournalLineSubDocument`,
  and `MongoJournalRepo`.
- `src/pyledger/infrastructure/mongo/posting/__init__.py` re-exports `PostingDocument` and `MongoPostingRepo`.
- `src/pyledger/infrastructure/mongo/shared/__init__.py` re-exports `TimestampedDocument` and `MongoExecutor`.
- `src/pyledger/shared/errors/__init__.py` re-exports `ErrorCode`, `FieldViolation`, `AppError`,
  `ValidationAppError`, `pydantic_error`, `PYDANTIC_CODES`, and `get_field_violations`.
- `src/pyledger/cli/features/account/__init__.py`, `src/pyledger/cli/features/journal/__init__.py`, and
  `src/pyledger/cli/features/posting/__init__.py` each re-export their feature's Typer `app`.
- `src/pyledger/cli/shared/ui/__init__.py` re-exports `panel`, `rule`, `table`, and `console`.
- `src/pyledger/cli/shared/interaction/__init__.py` re-exports `ask`, `select`, and `confirm`.
- `src/pyledger/cli/shared/errors/__init__.py` re-exports `ERRORS`, `HINTS`, `ErrorDetail`, and `FIELD_LABELS`.
- `src/pyledger/cli/shared/formatters/__init__.py` re-exports `FormattedError`, `build_error_panels`,
  `format_app_error`, `format_validation_errors`, and `format_validation_app_error`.
- `src/pyledger/shared/__init__.py` and `src/pyledger/__init__.py` are empty today.

## Dependency Direction

The live dependency direction is:

```text
main.py -> cli.bootstrap.build_context() -> cli.context.CliContext
main.py -> cli.state.CliState -> cli.app (Typer dispatch, via BlockingPortal)
cli.app -> cli.features.*.command -> cli.features.*.{parser,prompt} -> DTOs
cli.features.*.command -> cli.state.CliState.call(...) -> cli.features.*.handler
cli.features.*.handler -> cli.context.CliContext -> modules.*.service
cli.features.*.command -> cli.features.*.formatter -> cli.shared.ui
cli.features.*.command -> cli.shared.error_boundary -> cli.shared.formatters.error + cli.shared.errors + cli.shared.ui
modules.*.service -> modules.*.repo + modules.*.schemas + modules.*.dtos + shared.errors + peer services when needed
modules.*.schemas -> shared.rule + shared.errors
src/pyledger/conftest.py -> tests/fixtures/*
shared.* -> stdlib + pydantic
tests -> public modules + tests/fixtures + tests/factories + tests/fakes
config.* -> pydantic-settings + stdlib
infrastructure.mongo.* -> config.* + pymongo + beanie + shared.errors
infrastructure.mongo.posting.* -> infrastructure.mongo.shared + modules.posting.* + shared.rule + shared.errors
```

Important boundary rules:

- CLI code should not make accounting decisions.
- Feature modules should not import Rich or Typer.
- Shared validation helpers should not depend on CLI presentation code.
- Repositories must remain behind interfaces.
- `cli.features.*.handler` must not import Typer, Click, or Rich.
- `cli.features.*.formatter` must not import repositories, services, or domain schemas — only DTOs/ViewModels.
- No command, service, or repository may open a second `BlockingPortal` or event loop; `main.py` opens exactly one for the life of the process.

## Layer Boundaries

### CLI Layer

Location:

- `src/pyledger/main.py`
- `src/pyledger/cli/`

Responsibilities:

- define the Typer application and its composition root,
- register feature command groups,
- bridge synchronous Typer dispatch onto the CLI's single async event loop,
- resolve raw input (CLI flags or interactive prompts) into validated DTOs,
- render accounting output and validation errors via Rich,
- keep user interaction separate from accounting rules.

Current state:

- `main.py::main()` builds the production `CliContext` via `bootstrap.build_context()` and calls `run()`, which
  opens the CLI's one `BlockingPortal`, constructs `CliState`, dispatches `app(obj=state)` synchronously, and
  guarantees `context.aclose()` runs in a `finally` block regardless of outcome.
- `cli/app.py` creates the root Typer app, registers the `account`, `journal`, and `posting` sub-apps, and defines
  a defensive `main_callback()` that builds a fallback `CliContext` only when `ctx.obj` is `None` (never true for a
  real invocation dispatched through `main.py`).
- `cli/bootstrap.py::build_context()` is the CLI's single composition root; constructing a `CliContext` performs
  no I/O.
- `cli/context.py::CliContext` lazily creates and caches the shared MongoDB connection, repositories, and services
  for one CLI invocation, translating connection failures to `AppError.storage_timeout()`/
  `AppError.storage_unavailable()`.
- `cli/state.py::CliState` pairs a `CliContext` with a `BlockingPortal` and exposes `state.call(...)` as the only
  sanctioned bridge from a synchronous command into async service/repository code.
- `cli/features/{account,journal,posting}/` each implement the full `command.py` → `parser.py`/`prompt.py` →
  `handler.py` → `formatter.py` pipeline for their feature, fully wired to `AccountService`, `JournalService`, and
  `PostingService` respectively.
- `cli/shared/error_boundary.py` is fully wired into every command: it catches `AppError`, `ValidationAppError`,
  and raw `pydantic.ValidationError`, formats them via `cli/shared/formatters/error.py` and the CLI-owned catalogs
  in `cli/shared/errors/`, prints Rich panels, and exits with code 1.
- `cli/shared/ui/` provides the shared themed `console` singleton and the `panel`/`rule`/`table` widget factories
  used by every feature's formatter.

For the full CLI architecture — layer-by-layer responsibilities, the async execution model, the command lifecycle,
and the feature-extension guide — see `src/pyledger/cli/README.md`.

### Configuration Layer

Location:

- `src/pyledger/config/`

Responsibilities:

- Define typed settings models (`Settings`, `TestSettings`, `MongoSettings`).
- Load configuration from environment variables and optional dotenv files.
- Provide a cached `get_settings()` accessor for the rest of the application.
- Keep test configuration isolated from production configuration.

Current state:

- `Settings` loads from `PYLEDGER_` environment variables and an optional `.env` file.
- `TestSettings` loads from `PYLEDGER_TEST_` environment variables and an optional `.env.test` file.
- `MongoSettings` is nested inside both settings models and carries `uri` and `db` fields.
- `get_settings()` uses `lru_cache`; the cache is cleared in `tests/fixtures/settings.py` before and after every
  test via `isolate_settings_cache`.

### Infrastructure Layer

Location:

- `src/pyledger/infrastructure/`
- `src/pyledger/infrastructure/mongo/`

Responsibilities:

- Provide MongoDB connection lifecycle management.
- Supply the `MongoConnection` dataclass for passing connection resources to future repository adapters.
- Keep database concerns outside domain models, services, and CLI code.

Current state:

- `connect()` creates an `AsyncMongoClient`, verifies connectivity with a ping, and returns a `MongoConnection`.
- `disconnect()` closes the client held by a `MongoConnection`.
- `infrastructure/mongo/shared/` provides `TimestampedDocument`, `MongoExecutor`, and the shared MongoDB error
  translation helper.
- `infrastructure/mongo/account/` provides `AccountDocument` and the concrete `MongoAccountRepo` implementation.
- `infrastructure/mongo/journal/` provides `JournalDocument`, `JournalLineSubDocument`, and the concrete
  `MongoJournalRepo` implementation.
- `infrastructure/mongo/posting/` provides `PostingDocument` and the concrete `MongoPostingRepo` implementation.
- `infrastructure/mongo/tests/`, `infrastructure/mongo/account/tests/`, `infrastructure/mongo/journal/tests/`, and
  `infrastructure/mongo/posting/tests/` cover the MongoDB connection helpers and the account, journal, and posting
  repository adapters.

Boundary rules:

- Infrastructure code must not import from `cli/` or `modules/`.
- Domain models must not import from `infrastructure/`.
- `connect()` and `disconnect()` accept `MongoSettings`; they do not access `get_settings()` directly.
- The Mongo infrastructure layer should not couple services to `AsyncMongoClient` or other storage-driver types.

### Feature Modules

Location:

- `src/pyledger/modules/`

Responsibilities:

- hold the accounting models,
- hold feature-specific validation rules,
- define service orchestration,
- define repository contracts,
- provide DTOs for service boundaries.

This is where the current accounting domain lives.

### Shared Support

Location:

- `src/pyledger/shared/`

Responsibilities:

- provide reusable validation helpers,
- provide account lookup normalization,
- define the shared error model,
- translate Pydantic errors into domain errors.

`shared/util.py` currently contains `default_posting_date()`, but it is not used by the active workflow.

## Responsibility Map

### `src/pyledger/main.py`

- Console-script entry point.
- Imports and invokes the Typer app.
- Does not contain active accounting logic.

### `src/pyledger/cli/app.py`

- Constructs the root Typer application.
- Owns CLI-level configuration.
- Registers the journal command namespace.

### `src/pyledger/cli/features/{account,journal,posting}/command.py`

- Defines each feature's Typer command group (`account`: create/get/list/update/delete; `journal`: create/get/list;
  `posting`: post/get-by-account/get-by-journal).
- Resolves input via the feature's own `parser.py`/`prompt.py`, dispatches to `handler.py` via
  `state.call(...)` inside `error_boundary()`, and renders results via `formatter.py`.
- Never calls a repository or service directly, never constructs a domain model, never renders Rich components
  outside its own formatter.

### `src/pyledger/cli/shared/ui/console.py`

- Creates the shared Rich console instance.
- Installs traceback styling.

### `src/pyledger/cli/shared/ui/theme/*`

- Defines terminal theme detection and style names.
- Keeps style selection separate from rendering code.

### `src\pyledger\cli\shared\ui\widgets.py`

- Builds reusable Rich panels, rules, and tables.
- Keeps layout choices out of the feature formatters.

### `src/pyledger/cli/shared/error_boundary.py`, `cli/shared/formatters/error.py`, `cli/shared/errors/{errors,hint}.py`

- `error_boundary.py` is the CLI's single error-handling seam, wrapping one `state.call(...)` per command.
- `formatters/error.py` converts `pydantic.ValidationError`, `AppError`, and `ValidationAppError` into
  `FormattedError` instances and Rich panels — no terminal I/O of its own.
- `errors/errors.py` and `errors/hint.py` are the CLI-owned message and hint catalogs, keyed by `ErrorCode`,
  kept deliberately separate from `shared/errors` so presentation wording never leaks into the domain error model.
- Fully wired into every command in every feature group — this is no longer a dormant or partially-used path.

### `src/pyledger/modules/account/schemas/account.py`

- Defines `AccountCategory`.
- Defines `Account`.
- Derives `normal_balance` from category.
- Normalizes account names.

### `src/pyledger/modules/account/schemas/chart.py`

- Defines `ChartOfAccounts`.
- Builds code and name indexes.
- Resolves canonical names case-insensitively with `get_by_name()`.
- Resolves account codes directly with `get_by_code()`.
- Does not expose a `resolve()` method.

### `src/pyledger/modules/account/dtos.py`

- Defines create, update, and view DTOs for account workflows.

### `src/pyledger/modules/account/repo.py`

- Defines the async account repository contract.
- `MongoAccountRepo` in `infrastructure/mongo/account/` implements the contract.

### `src/pyledger/modules/account/service.py`

- Orchestrates account creation, update, lookup, listing, resolution, and deletion.
- Converts validated accounts into view models.
- Rebuilds the chart of accounts when a full snapshot is needed.

### `src/pyledger/modules/journal/schemas/line.py`

- Defines `JournalLine`.
- Enforces debit/credit exclusivity.
- Normalizes account references.

### `src/pyledger/modules/journal/schemas/journal.py`

- Defines `JournalEntry`.
- Enforces balanced entries and a minimum line count.
- Computes totals and balance state.

### `src/pyledger/modules/journal/dtos.py`

- Defines `JournalLineInput`, `CreateJournalInput`, `JournalLineViewModel`, and `JournalViewModel`.
- Input DTOs perform structural validation only; accounting rules are enforced when the service constructs domain
  models.
- `CreateJournalInput` does not carry `journal_number`; `JournalService` assigns it via the repository.

### `src/pyledger/modules/journal/service.py`

- Validates account references against a chart snapshot from `AccountService`.
- Requests journal numbers from `JournalRepo`.
- Builds `JournalEntry` and returns `JournalViewModel`.
- Exposes `create_journal_entry()`, `get_journal_entry()`, and `list_journal_entries()`.
- Includes private mapping helpers `_to_line_view()` and `_to_entry_view()`.

### `src/pyledger/modules/journal/repo.py`

- Defines the async journal repository contract.
- Requires `save()`, `get_by_number()`, `list_entries()`, and `next_journal_number()`.
- `MongoJournalRepo` in `infrastructure/mongo/journal/` implements the contract.

### `src/pyledger/modules/journal/rule.py`

- Present as an empty scaffold.
- No journal-specific rule helpers are defined yet.

### `src/pyledger/modules/posting/schemas/ledger_posting.py`

- Defines `LedgerPosting`.
- Makes postings immutable.
- Validates account names, amounts, and posting dates.

### `src/pyledger/modules/posting/dtos.py`

- Defines `PostingViewModel`.
- Debit postings carry a non-None `debit_amount` and a None `credit_amount`; credit postings are the reverse.
- `is_debit` is a `computed_field` derived from `debit_amount` so it cannot diverge from the stored amounts.
- There is no input DTO; postings are derived internally by `PostingService` from `JournalViewModel` instances.

### `src/pyledger/modules/posting/service.py`

- Implements `PostingService`.
- Exposes `post_journal_entry()`, `get_postings_by_account()`, and `get_postings_by_journal_number()`.
- Derives one `LedgerPosting` per journal line from a `JournalViewModel` returned by `JournalService`.
- Enforces the one-posting-per-journal-entry invariant by checking `PostingRepo.get_by_journal_number()` before saving.
- Delegates posting batch persistence to `PostingRepo.save_many()`.
- Returns `PostingViewModel` instances to callers.

### `src/pyledger/modules/posting/repo.py`

- Defines the async posting repository contract with `save_many()`, `get_by_account()`, and `get_by_journal_number()`.
- `MongoPostingRepo` in `infrastructure/mongo/posting/` implements the contract.

### `src/pyledger/modules/posting/rule.py`

- Present as an empty scaffold.
- No posting-specific rule helpers are defined yet.

## Domain Model Structure

### Account

The account model is responsible for:

- validating the account code,
- validating and normalizing the name,
- deriving normal balance from category.

The current model does not include aliases.

### ChartOfAccounts

The chart aggregate is responsible for:

- uniqueness of account codes,
- uniqueness of account names,
- case-insensitive account lookup by canonical name,
- direct account lookup by code,
- efficient lookup caching via private indexes.

### JournalLine

The line model is responsible for:

- account normalization,
- side exclusivity,
- rejecting negative amounts.

### JournalEntry

The entry model is responsible for:

- minimum line count,
- journal number validation,
- posting date validation,
- aggregate debit and credit totals,
- balance enforcement.

### LedgerPosting

The posting model is responsible for:

- freezing derived posting data,
- carrying the source journal number and date,
- validating the account reference,
- validating single-side posting amounts.

## Repository Architecture

Repository abstractions exist as contracts, and the account, journal, and posting contracts now have concrete MongoDB adapters.

Implemented contracts:

- `AccountRepo`
- `JournalRepo`
- `PostingRepo`

Implemented adapters:

- `MongoAccountRepo`
- `MongoJournalRepo`
- `MongoPostingRepo`

Architectural intent:

- repositories should remain async,
- repositories should not contain business rules,
- repositories should not know about Rich or Typer,
- repositories should be swappable for future storage adapters.

## Service Architecture

The service layer exists inside each feature package rather than in a separate top-level application package.

Current services:

- `AccountService`
- `JournalService`
- `PostingService`

Service responsibilities:

- orchestrate domain model construction,
- call repository abstractions,
- translate validation failures into application errors,
- return DTOs or derived models to callers.

Service boundaries:

- services are the correct place for cross-aggregate orchestration,
- services should not render output,
- services should not own persistence details,
- services should keep the CLI thin.

Current shape:

- `AccountService` is complete end to end.
- `JournalService` is complete end to end for create, get, and list workflows.
- `PostingService` is implemented end to end for journal-to-posting derivation, duplicate-posting prevention, and retrieval by account or journal number.
- `MongoJournalRepo` is implemented end to end for journal persistence, lookup, list, and journal-number allocation.
  Duplicate journal-number collisions translate to `ErrorCode.DUPLICATE_JOURNAL_NUMBER`.
- `MongoPostingRepo` is implemented end to end for posting persistence, lookup by account, and lookup by journal number.
  Posting batches are persisted with `save_many()` and reconstructed from `PostingDocument` records.

## DTO Architecture

DTOs separate caller input and output contracts from domain schemas.

Current DTO coverage:

- Account: `CreateAccountInput`, `UpdateAccountInput`, `AccountViewModel`, `ChartOfAccountsViewModel`.
- Journal: `JournalLineInput`, `CreateJournalInput`, `JournalLineViewModel`, `JournalViewModel`.
- Posting: `PostingViewModel` only. Posting inputs are not modeled because postings are derived from validated journal entries.

View models are what CLI formatters consume. Input DTOs are what future commands and API routes would pass into
services.

## Journal Architecture

Current journal support is split across five layers:

1. Domain schemas (`JournalLine`, `JournalEntry`) enforce accounting rules at construction time.
2. Input and view DTOs define the service boundary shape.
3. `JournalService` validates account references, allocates journal numbers, creates `JournalEntry`, persists it,
   fetches entries, and returns view models.
4. `JournalRepo` is the async persistence boundary used by the service.
5. `MongoJournalRepo` persists and reconstructs journal entries in MongoDB, translating duplicate journal-number
   collisions to `ErrorCode.DUPLICATE_JOURNAL_NUMBER`.
6. `journal_fmt.py` renders view models for terminal output.

There is no CLI command that creates or lists journal entries yet.

## Posting Architecture

Current posting support includes a live service layer and MongoDB adapter, not just a schema and repository contract:

1. `LedgerPosting` validates immutable single-side posting records.
2. `PostingViewModel` is the read-only output DTO for posting workflows.
3. `PostingRepo` defines async persistence and lookup methods.
4. `PostingService` retrieves a journal entry from `JournalService`, prevents duplicate posting by checking
   `get_by_journal_number()`, derives one `LedgerPosting` per journal line, saves the batch, and returns
   `PostingViewModel` instances.
5. `PostingDocument` is the MongoDB persistence model for `LedgerPosting` records.
6. `MongoPostingRepo` translates between `LedgerPosting` and `PostingDocument`, uses decimal-string storage, and
   preserves journal-line order with `line_index`.
7. `tests/factories/posting.py`, `tests/fakes/posting_repo.py`, `tests/fixtures/posting.py`, and
   `tests/fixtures/mongo.py` provide the service factory, in-memory fake, and MongoDB fixtures used by posting tests.

`modules/posting/rule.py` remains an empty scaffold. There is still no posting input DTO, and the CLI does not yet
expose posting commands.

## Error Architecture

The error system is split between shared domain errors and CLI presentation.

### Shared Error Model

`src/pyledger/shared/errors/` defines:

- `ErrorCode`
- `AppError`
- `ValidationAppError`
- `FieldViolation`
- Pydantic translation helpers

The shared error model also includes storage-specific helpers such as
`AppError.storage_unavailable()` and `AppError.storage_timeout()` so
MongoDB connection failures can cross the repository boundary as
structured application errors.

This layer provides stable error identity and structured context.

### CLI Error Rendering

`src/pyledger/cli/constants/errors.py` defines:

- user-facing error messages,
- user-facing hints,
- field labels for presentation.

`src/pyledger/cli/formatters/error_fmt.py` turns validation and application errors into terminal output.

### Boundary Rule

The shared error layer should not contain presentation text. The CLI layer owns the wording that users see.

## Validation Architecture

Validation is implemented in three layers:

1. Shared reusable rules in `shared/rule.py`.
2. Pydantic field and model validators inside the feature schemas.
3. Service-level validation and existence checks where cross-record rules are required.

Current examples:

- `clean_account_name()` normalizes account references.
- `is_valid_line_amounts()` enforces one-sided journal lines.
- `Account.validate_name()` enforces account naming rules.
- `ChartOfAccounts` enforces name and code uniqueness.
- `JournalEntry` enforces date, line-count, and balance rules.
- `JournalService` validates account references before entry construction.
- `LedgerPosting` enforces frozen single-side postings.

## Test Architecture

Testing currently focuses on domain behavior, shared error translation, shared rules, account/journal/posting service
workflows, and MongoDB infrastructure behavior.

Current coverage:

- account model rules,
- chart-of-accounts uniqueness and lookup,
- account lookup key normalization,
- journal line validation,
- journal entry validation,
- journal DTO validation,
- journal service create/get/list workflows,
- ledger posting validation,
- posting DTO validation,
- posting service journal-to-posting workflows,
- posting repository mapping and MongoDB persistence behavior,
- shared error translation,
- shared rule helpers,
- account service workflows.

Current test organization:

- `src/pyledger/modules/account/tests/`
- `src/pyledger/modules/journal/tests/`
- `src/pyledger/modules/posting/tests/`
- `src/pyledger/shared/errors/tests/`
- `src/pyledger/shared/tests/`
- `src/pyledger/infrastructure/mongo/posting/tests/`
- root `tests/fixtures/`
- root `tests/factories/`
- root `tests/fakes/`

The root `tests/` package provides shared fixtures, factories, and fake repository implementations rather than test
cases.

`src/pyledger/conftest.py` registers the shared fixture modules.
`tests/fakes/journal_repo.py` provides an in-memory `JournalRepo` that issues journal numbers sequentially for service
tests.
`tests/fakes/posting_repo.py` provides an in-memory `PostingRepo` for posting-service tests.
`tests/factories/posting.py` provides posting service and domain-object factories for posting tests.
`tests/fixtures/posting.py` provides posting-domain fixtures, a `MongoPostingRepo` fixture, and a `PostingDocument`
stub for unit tests that construct `PostingDocument` instances without Beanie initialization.

`tests/fixtures/journal.py` provides journal domain fixtures, a `MongoJournalRepo` fixture, and a stub that lets unit
tests construct `JournalDocument` without Beanie initialization.
`tests/fixtures/mongo.py` registers `AccountDocument`, `JournalDocument`, and `PostingDocument` with Beanie and
truncates the collections used by MongoDB integration tests.
`src/pyledger/infrastructure/mongo/tests/`, `src/pyledger/infrastructure/mongo/account/tests/`,
`src/pyledger/infrastructure/mongo/journal/tests/`, and `src/pyledger/infrastructure/mongo/posting/tests/` cover the
MongoDB connection helpers and the account, journal, and posting repository adapters.

CLI workflow tests exist end-to-end for `account`, `journal`, and `posting`, split into fake-backed unit tests
and MongoDB-backed integration tests per feature, plus dedicated composition-root tests for `CliContext`,
`CliState`, `bootstrap.build_context()`, and `app.py` under `src/pyledger/cli/tests/`. There are still no
reporting tests, since no reporting pipeline exists yet.

## Application Flow

The current executable flow is:

1. The `pyledger` console script imports `pyledger.main:main`.
2. `main.py::main()` builds the production `CliContext` and calls `run()`, which opens the CLI's single
`BlockingPortal`, constructs `CliState`, and dispatches the Typer application via `app(obj=state)`.
3. Typer dispatches into the matched feature command group (`account`, `journal`, or `posting`).
4. The command resolves input via its feature's `parser.py` (CLI flags) or `prompt.py` (interactive), builds a
DTO, and calls its `handler.py` via `state.call(...)`.
5. The handler resolves the relevant service from `CliContext` and calls it. `AccountService`, `JournalService`,
and `PostingService` build or validate domain models and coordinate repository access.
6. On success, the service returns a ViewModel, which the command renders via its feature's `formatter.py`
through the shared Rich `console`.
7. On failure, `error_boundary()` catches `AppError/ValidationAppError/pydantic.ValidationError`, formats
them via `cli/shared/formatters/error.py` and the CLI-owned catalogs, prints Rich panels, and exits with
code 1.
8. `context.aclose()` runs in a finally block in `main.py::run()`, regardless of outcome.

This flow is now fully implemented and user-facing for account, journal, and posting workflows — it is no longer
structural-only.

## Implementation Status

### Implemented

- Typer application bootstrap.
- Rich console and theme scaffolding.
- Shared validation rules.
- Shared error model and Pydantic translation helpers.
- Account domain model and chart-of-accounts model.
- Journal line and journal entry models.
- Journal input and view DTOs.
- Posting view DTO.
- Journal repository contract.
- Posting repository contract.
- Journal service workflows.
- Posting service workflows.
- Ledger posting model.
- Account service.
- Journal entry formatter.
- Journal and posting domain schema tests.
- Journal DTO tests.
- Posting DTO tests.
- Journal service tests.
- Posting service tests.
- `AccountRepo`, `JournalRepo`, and `PostingRepo` contracts.
- Typed configuration layer (`Settings`, `TestSettings`, `MongoSettings`, `get_settings()`)
- MongoDB connection bootstrap (`connect()`, `disconnect()`, `MongoConnection`)
- MongoDB account repository adapter (`AccountDocument`, `MongoAccountRepo`, `MongoExecutor`)
- MongoDB journal repository adapter (`JournalDocument`, `JournalLineSubDocument`, `MongoJournalRepo`)
- MongoDB posting repository adapter (`PostingDocument`, `MongoPostingRepo`)
- Settings tests
- MongoDB connection tests
- MongoDB account repository tests
- MongoDB journal repository tests
- MongoDB posting repository tests
- CLI error formatting.
- CLI error presentation constants.
- CLI command wiring beyond the journal group scaffold.
- CLI composition root (`bootstrap.build_context()`, `CliContext`, `CliState`)
- CLI account, journal, and posting command groups, fully wired to their respective services
- CLI parser/prompt/handler/formatter layering for all three feature groups
- CLI shared error boundary, error formatting, and error/hint catalogs
- CLI shared Rich UI (console, theme, widgets)
- CLI unit and integration test suites for all three feature groups
- CLI composition-root tests (`CliContext`, `CliState`, `build_context()`, `app.py`)

### Partial

(none currently — CLI implementation is complete for account, journal, and posting workflows)

### Scaffold Only

- `modules/journal/rule.py`
- `modules/posting/rule.py`

### Planned

- Trial balance reporting.
- Account, journal, and posting CLI workflows.
- Higher-level reports and historical views.
- Import/export and integration surfaces.

## Known Gaps

- Alias support is not implemented.
- The CLI invalid-account-name and unknown-account copy still mentions abbreviations and aliases, which does not match
  the active validator or chart lookup behavior.
- `MongoPostingRepo.save_many()` uses a batch `insert_many()` call without transaction support, so a mid-batch
  interruption can partially persist a journal's postings and concurrent posting attempts can still race.
- There is no trial balance or reporting pipeline.
- `modules/posting/rule.py` is still an empty scaffold.
- There are no operational CLI commands yet.
