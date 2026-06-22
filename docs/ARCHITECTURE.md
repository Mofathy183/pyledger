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
├── __init__.py
├── main.py
├── cli/
│   ├── __init__.py
│   ├── app.py
│   ├── console.py
│   ├── commands/
│   │   ├── __init__.py
│   │   └── journal_cmd.py
│   ├── constants/
│   │   ├── __init__.py
│   │   └── errors.py
│   ├── formatters/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── error_fmt.py
│   │   └── journal_fmt.py
│   └── theme/
│       ├── __init__.py
│       ├── detection.py
│       └── styles.py
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
├── conftest.py
├── fixtures/
├── factories/
└── fakes/
```

There is no `src/pyledger/conftest.py`, no `tests/helpers.py`, and no `src/pyledger/cli/tests/` directory.

## Public Exports

- `src/pyledger/modules/account/__init__.py` re-exports `AccountRepo`, `AccountService`, `CreateAccountInput`,
  `UpdateAccountInput`, `AccountViewModel`, and `ChartOfAccountsViewModel`.
- `src/pyledger/modules/journal/__init__.py` re-exports `JournalRepo`, `JournalService`, `CreateJournalInput`,
  `JournalLineInput`, `JournalLineViewModel`, and `JournalViewModel`.
- `src/pyledger/cli/constants/__init__.py` re-exports `ERRORS`, `HINTS`, and `FIELD_LABELS`.
- `src/pyledger/modules/posting/__init__.py`, `src/pyledger/cli/formatters/__init__.py`, `src/pyledger/shared/__init__.py`,
  and `src/pyledger/__init__.py` are empty today.

## Dependency Direction

The live dependency direction is:

```text
main.py -> cli.app -> cli.commands -> cli.formatters -> modules.*.dtos/schemas/services -> shared.*
modules.*.service -> modules.*.repo + modules.*.schemas + modules.*.dtos + shared.errors + peer services when needed
modules.*.schemas -> shared.rule + shared.errors
shared.* -> stdlib + pydantic
tests -> public modules + tests/fixtures + tests/factories + tests/fakes
```

Important boundary rules:

- CLI code should not make accounting decisions.
- Feature modules should not import Rich or Typer.
- Shared validation helpers should not depend on CLI presentation code.
- Repositories must remain behind interfaces.

## Layer Boundaries

### CLI Layer

Location:

- `src/pyledger/main.py`
- `src/pyledger/cli/`

Responsibilities:

- define the Typer application,
- register command groups,
- render accounting output,
- render validation errors,
- keep user interaction separate from accounting rules.

Current state:

- `main.py` boots the Typer app. Commented legacy command code remains in the file but references removed
  `pyledger.core` modules and is not active.
- `cli/app.py` creates the root app and registers the `journal` sub-app.
- `cli/commands/journal_cmd.py` defines a command namespace but no operational subcommands.
- `cli/formatters/journal_fmt.py` renders journal entries and journal lists from view models.
- `cli/formatters/error_fmt.py` and `cli/constants/errors.py` exist but are not wired into a live command path.
- `cli/console.py` configures the Rich console.

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
- Contains commented legacy scaffold code that is not executed.
- Does not contain active accounting logic.

### `src/pyledger/cli/app.py`

- Constructs the root Typer application.
- Owns CLI-level configuration.
- Registers the journal command namespace.

### `src/pyledger/cli/commands/journal_cmd.py`

- Defines the `journal` command group.
- Currently a scaffold with no subcommands.

### `src/pyledger/cli/console.py`

- Creates the shared Rich console instance.
- Installs traceback styling.

### `src/pyledger/cli/theme/*`

- Defines terminal theme detection and style names.
- Keeps style selection separate from rendering code.

### `src/pyledger/cli/formatters/base.py`

- Builds reusable Rich panels, rules, and tables.
- Keeps layout choices out of the feature formatters.

### `src/pyledger/cli/formatters/journal_fmt.py`

- Renders journal entries and journal lists.
- Consumes `JournalViewModel` and `JournalLineViewModel`.

### `src/pyledger/cli/formatters/error_fmt.py`

- Formats validation and application errors for terminal output.
- Uses CLI-owned message and hint catalogs.
- Is currently unused by any operational command.

### `src/pyledger/cli/constants/errors.py`

- Defines CLI-facing error messages, hints, and field labels.
- Is currently only consumed by `cli/formatters/error_fmt.py`.
- Still mentions abbreviations and aliases in several messages even though alias support is not implemented.

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
- No concrete implementation exists in the repository.

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
- No concrete implementation exists in the repository.

### `src/pyledger/modules/journal/rule.py`

- Present as an empty scaffold.
- No journal-specific rule helpers are defined yet.

### `src/pyledger/modules/posting/schemas/ledger_posting.py`

- Defines `LedgerPosting`.
- Makes postings immutable.
- Validates account names, amounts, and posting dates.

### `src/pyledger/modules/posting/dtos.py`

- Present as an empty scaffold.
- No posting input or view DTOs are defined yet.

### `src/pyledger/modules/posting/service.py`

- Present as commented scaffold code.
- References a stale `chart.resolve()` API and is not executable.

### `src/pyledger/modules/posting/repo.py`

- Defines the async posting repository contract with `save_many()`, `get_by_account()`, and `get_by_journal_number()`.
- No concrete implementation exists in the repository.

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

Repository abstractions currently exist only as contracts.

Implemented contracts:

- `AccountRepo`
- `JournalRepo`
- `PostingRepo`

Not yet implemented:

- any storage-backed repository adapter

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
- `PostingService` is commented scaffold code and should not be treated as implemented behavior.

## DTO Architecture

DTOs separate caller input and output contracts from domain schemas.

Current DTO coverage:

- Account: `CreateAccountInput`, `UpdateAccountInput`, `AccountViewModel`, `ChartOfAccountsViewModel`.
- Journal: `JournalLineInput`, `CreateJournalInput`, `JournalLineViewModel`, `JournalViewModel`.
- Posting: none defined yet (`modules/posting/dtos.py` is empty).

View models are what CLI formatters consume. Input DTOs are what future commands and API routes would pass into
services.

## Journal Architecture

Current journal support is split across five layers:

1. Domain schemas (`JournalLine`, `JournalEntry`) enforce accounting rules at construction time.
2. Input and view DTOs define the service boundary shape.
3. `JournalService` validates account references, allocates journal numbers, creates `JournalEntry`, persists it,
   fetches entries, and returns view models.
4. `JournalRepo` is the async persistence boundary used by the service.
5. `journal_fmt.py` renders view models for terminal output.

There is no journal storage adapter and no CLI command that creates or lists journal entries yet.

## Posting Architecture

Current posting support is limited to the domain model and a repository contract:

1. `LedgerPosting` validates immutable single-side posting records.
2. `PostingRepo` defines async persistence and lookup methods.
3. The commented `PostingService` sketch describes intended posting derivation from journal entries, but it is not
   executable and references APIs that no longer exist.

There is no posting DTO layer, no active posting service, and no workflow that converts journal entries into ledger
postings.

## Error Architecture

The error system is split between shared domain errors and CLI presentation.

### Shared Error Model

`src/pyledger/shared/errors/` defines:

- `ErrorCode`
- `AppError`
- `ValidationAppError`
- `FieldViolation`
- Pydantic translation helpers

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

Testing currently focuses on domain behavior, shared error translation, shared rules, and account/journal service
workflows.

Current coverage:

- account model rules,
- chart-of-accounts uniqueness and lookup,
- account lookup key normalization,
- journal line validation,
- journal entry validation,
- journal DTO validation,
- journal service create/get/list workflows,
- ledger posting validation,
- shared error translation,
- shared rule helpers,
- account service workflows.

Current test organization:

- `src/pyledger/modules/account/tests/`
- `src/pyledger/modules/journal/tests/`
- `src/pyledger/modules/posting/tests/`
- `src/pyledger/shared/errors/tests/`
- `src/pyledger/shared/tests/`
- root `tests/fixtures/`
- root `tests/factories/`
- root `tests/fakes/`

The root `tests/` package provides shared fixtures, factories, and fake repository implementations rather than test
cases.

`tests/fakes/journal_repo.py` provides an in-memory `JournalRepo` that issues journal numbers sequentially for service
tests.

There are no tests for concrete storage, reporting, posting service workflows, or end-user CLI commands yet.

## Application Flow

The current executable flow is:

1. The `pyledger` console script imports `pyledger.main:main`.
2. `main.py` invokes the Typer application.
3. Typer dispatches into the registered command groups.
4. Command handlers would construct DTOs and call feature services.
5. `AccountService` and `JournalService` build or validate domain models and coordinate repository access.
6. Shared error translation converts validation failures into structured errors.
7. CLI formatters render view models or error objects with Rich.

The CLI currently stops at the scaffold stage for operational commands, so the flow is mostly structural rather than
user-facing.

## Implementation Status

### Implemented

- Typer application bootstrap.
- Rich console and theme scaffolding.
- Shared validation rules.
- Shared error model and Pydantic translation helpers.
- Account domain model and chart-of-accounts model.
- Journal line and journal entry models.
- Journal input and view DTOs.
- Journal repository contract.
- Journal service workflows.
- Ledger posting model.
- Account service.
- Journal entry formatter.
- Journal and posting domain schema tests.
- Journal DTO tests.
- Journal service tests.
- `AccountRepo`, `JournalRepo`, and `PostingRepo` contracts.

### Partial

- CLI error formatting.
- CLI error presentation constants.
- CLI command wiring beyond the journal group scaffold.
- Posting service scaffold.

### Scaffold Only

- `modules/journal/rule.py`
- `modules/posting/dtos.py`
- `modules/posting/rule.py`
- `modules/posting/service.py`

### Planned

- Concrete repository implementations.
- Storage adapters.
- Posting service workflows and posting DTOs.
- Trial balance reporting.
- Account, journal, and posting CLI workflows.
- Higher-level reports and historical views.
- Import/export and integration surfaces.

## Known Gaps

- Alias support is not implemented.
- The CLI invalid-account-name and unknown-account copy still mentions abbreviations and aliases, which does not match
  the active validator or chart lookup behavior.
- There is no concrete storage implementation.
- There is no journal or posting storage adapter.
- There is no trial balance or reporting pipeline.
- There are no operational CLI commands yet.
- The commented `PostingService` scaffold references `chart.resolve()`, which does not exist.
