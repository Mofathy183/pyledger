# PyLedger Architecture

## Purpose

This document describes the current architecture of PyLedger and the direction of the codebase as it grows into a
fuller bookkeeping system. It separates what exists today from the layers that are planned next so the repository
remains easy to evolve without mixing business logic, I/O, and reporting concerns.

PyLedger follows a clean-architecture style approach:

- domain logic stays in `core/`,
- CLI concerns stay in `cli/`,
- shared formatting and presentation helpers stay in `utils/`,
- persistence and reporting are expected to live in separate layers as the project expands.

## Current Architecture

The current repository is intentionally small. It contains a small set of domain models, one Typer application, and a
set of utility modules that support validation output and terminal formatting.

### Current Folder Structure

```text
src/pyledger/
├── __init__.py
├── main.py
├── cli/
│   ├── __init__.py
│   ├── app.py
│   └── commands/
│       ├── __init__.py
│       └── journal_command.py
├── core/
│   ├── __init__.py
│   ├── errors.py
│   ├── helpers.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── account.py
│   │   └── journal.py
│   └── rules/
│       ├── __init__.py
│       └── journal_rules.py
└── utils/
    ├── __init__.py
    ├── console.py
    ├── constants.py
    └── formatter.py
```

### Current Test Structure

```text
tests/
├── __init__.py
├── conftest.py
├── helpers.py
├── core/
│   ├── models/
│   │   ├── test_account_model.py
│   │   └── test_journal_model.py
│   └── rules/
│       └── test_journal_rules.py
└── utils/
    └── test_formatter.py
```

Notes:

- `test_journal_model.py` covers `JournalLine` and `JournalEntry`.
- `test_journal_rules.py` covers account-name normalization and line-amount validation.
- `test_formatter.py` covers validation formatting and journal-entry rendering.
- `test_account_model.py` exists as a placeholder and does not yet contain assertions.
- There are no CLI tests yet.

### Current Responsibility Map

- `src/pyledger/main.py`
  - Application entry point.
  - Boots the Typer app and exposes the console command used by the installed script.

- `src/pyledger/cli/app.py`
  - Creates the Typer application instance.
  - Owns CLI configuration such as help text and command suggestion settings.
  - Should remain free of accounting rules.

- `src/pyledger/cli/commands/journal_command.py`
  - Defines the `journal` command namespace.
  - Currently acts as a scaffold only; there are no user-facing subcommands yet.

- `src/pyledger/core/errors.py`
  - Defines domain error codes, error messages, and validation helpers.
  - Keeps Pydantic-compatible custom errors centralized.

- `src/pyledger/core/helpers.py`
  - Provides small domain helpers such as default posting dates and journal number generation.
  - Keeps convenience logic near the accounting domain rather than in the CLI.

- `src/pyledger/core/models/account.py`
  - Defines the account category enum and the `Account` model.
  - Captures account metadata without mixing in CLI or formatting concerns.

- `src/pyledger/core/models/journal.py`
  - Defines `JournalLine` and `JournalEntry`.
  - Enforces journal-line validation, balanced entries, and computed totals.

- `src/pyledger/core/rules/journal_rules.py`
  - Provides reusable validation helpers for account names and journal-line amounts.
  - Keeps small rules independent of the Pydantic model classes that use them.

- `src/pyledger/utils/formatter.py`
  - Renders validation errors and journal-entry output for the terminal.
  - Keeps presentation formatting separate from core accounting rules.

- `src/pyledger/utils/console.py`
  - Configures Rich console behavior, theme selection, and traceback styling.
  - Centralizes terminal presentation concerns.

- `src/pyledger/utils/constants.py`
  - Stores message templates, field labels, hints, and presentation constants.
  - Supports consistent terminal output without embedding formatting data in business logic.

- `src/pyledger/__init__.py`
  - Marks the package and keeps the public import surface minimal.

- `src/pyledger/cli/__init__.py`
  - Package marker for CLI-related code.

- `src/pyledger/core/__init__.py`
  - Package marker for domain logic.

- `src/pyledger/utils/__init__.py`
  - Package marker for shared utilities.

## Layer Responsibilities

### Domain Layer

The domain layer is the center of the architecture. It should contain the accounting model, invariants, and business
rules that must remain true regardless of interface or storage mechanism.

#### Current location

```text
src/pyledger/core/
```

#### Current responsibilities

- Represent accounts, journal lines, and journal entries.
- Validate accounting constraints.
- Preserve double-entry rules.
- Keep business logic independent of CLI and formatting code.

#### Current module focus

- `errors.py`
  - Centralized validation error codes, details, and construction helpers.

- `helpers.py`
  - Date and journal-number helpers used by the accounting workflow.

- `models/account.py`
  - `AccountCategory`: account classification enum.
  - `Account`: domain model for account metadata.

- `models/journal.py`
  - `JournalLine`: a single posting line within a journal entry.
  - `JournalEntry`: a balanced journal record with computed debit and credit totals.

- `rules/journal_rules.py`
  - Account-name normalization.
  - Journal-line amount validation.

#### Architectural boundaries

- No Typer imports.
- No Rich imports.
- No file system access.
- No direct database or repository access.

The domain layer should be reusable from tests, CLI commands, future APIs, and future storage adapters.

### CLI Layer

The CLI layer is the user interface boundary. It should translate command-line input into domain objects, call the
appropriate application behavior, and render output to the terminal.

#### Current location

```text
src/pyledger/cli/
src/pyledger/main.py
```

#### Current responsibilities

- Configure the Typer application.
- Register command groups.
- Keep user interaction separate from accounting rules.
- Render validation and status output through presentation helpers.

#### Current module focus

- `app.py`
  - Defines the Typer application instance.
  - Keeps command registration separate from the main entry point.

- `commands/journal_command.py`
  - Defines the `journal` command group.
  - Does not yet expose operational journal commands.

- `main.py`
  - Wires the Typer app into executable form.
  - Serves as the `pyledger` console script target.

#### Architectural boundaries

- The CLI should not contain accounting rules.
- The CLI should not own storage logic.
- The CLI should not calculate ledger or trial balance behavior directly.
- The CLI should remain thin and delegate work to the core and future application layers.

### Utility Layer

The utility layer contains shared helpers that support presentation and convenience behaviors. These modules are not the
place for business rules, but they are appropriate for formatting, terminal setup, and generic helper functions used
across the user-facing application.

#### Current location

```text
src/pyledger/utils/
```

#### Current responsibilities

- Configure Rich console behavior.
- Standardize formatting and error display.
- Hold shared constants used by user-facing output.

#### Current module focus

- `console.py`
  - Sets up the global Rich console and theme map.
  - Installs traceback formatting for terminal debugging.

- `constants.py`
  - Stores validation message metadata and reason text.
  - Keeps display copy centralized.

- `formatter.py`
  - Formats validation errors into Rich panels.
  - Formats journal-entry data into Rich tables and summary panels.

#### Architectural boundaries

- Utilities should not own domain invariants.
- Utilities should not become a hidden service layer.
- Utilities may support presentation and lightweight shared behavior only.

## Domain Model

### Account

Represents a ledger account.

Attributes:

- code
- name
- category
- normal_balance
- aliases

### JournalLine

Represents a single posting line within a journal entry.

Attributes:

- account
- debit_amount
- credit_amount

Rules:

- A line cannot contain both a debit and credit amount.
- At least one amount must be greater than zero.
- Account names are normalized before the model is accepted.

### JournalEntry

Represents a complete accounting transaction.

Attributes:

- journal_number
- posting_date
- description
- lines

Computed properties:

- total_debits
- total_credits
- is_balanced

Rules:

- Must contain at least two `JournalLine` records.
- Total debits must equal total credits.
- The entry is valid only when `is_balanced` is true.

## Planned Architecture

PyLedger is expected to grow beyond the current prototype. The next layers should separate persistence, repositories,
and reporting from the core domain and CLI.

### Future Repository Layer

The repository layer will define abstract access patterns for persisted data. It should act as the boundary between
business logic and storage implementation.

#### Proposed location

```text
src/pyledger/repositories/
```

#### Planned responsibilities

- Define repository interfaces for journal entries, accounts, and ledger records.
- Expose persistence operations without binding the domain to a specific database or file format.
- Keep data access rules testable and swappable.

#### Typical responsibilities by module

- `journal_entry_repository.py`
  - Save and load journal entries.
  - Query entries by date, account, or journal number.

- `account_repository.py`
  - Store account metadata and account classifications.
  - Support account lookup and account catalog maintenance.

- `ledger_repository.py`
  - Persist posted ledger records or posting snapshots.
  - Support retrieval of account-level histories.

#### Boundary rules

- Repository interfaces should not format terminal output.
- Repository interfaces should not contain CLI parsing.
- Repository interfaces should avoid hard-coding storage technology.

### Future Storage Layer

The storage layer will provide concrete implementations of repository interfaces. This is where JSON files, SQLite, or
another durable store can be introduced without affecting domain rules.

#### Proposed location

```text
src/pyledger/storage/
```

#### Planned responsibilities

- Implement repository contracts.
- Serialize and deserialize domain data.
- Handle file, database, or other persistence mechanics.
- Keep storage-specific concerns isolated from the core accounting model.

#### Typical responsibilities by module

- `json_storage.py`
  - Read and write simple persisted data files.
  - Suitable for early local-first usage or export/import workflows.

- `sqlite_storage.py`
  - Provide structured persistence for journal entries, ledger postings, and report-ready data.
  - Support indexing and query-heavy workflows as the app matures.

- `mappers.py`
  - Convert between domain models and storage records.
  - Keep serialization rules in one place.

#### Boundary rules

- Storage code should not decide accounting rules.
- Storage code should not know about terminal formatting.
- Storage code should implement persistence, not policy.

### Future Reporting Layer

The reporting layer will transform domain and ledger data into user-facing accounting reports. It should consume
validated data and produce structured summaries that are separate from entry capture and persistence.

#### Proposed location

```text
src/pyledger/reports/
```

#### Planned responsibilities

- Build trial balances from ledger postings.
- Produce summaries and grouped account views.
- Support future financial statements and exports.
- Provide a stable reporting surface for the CLI or future integrations.

#### Typical responsibilities by module

- `trial_balance.py`
  - Aggregate account balances.
  - Verify that total debits and total credits match.

- `ledger_report.py`
  - Present account activity and posting detail.
  - Summarize transactions by account.

- `financial_statements.py`
  - Prepare higher-level outputs such as income statements or balance sheets when the domain supports them.

#### Boundary rules

- Reporting should depend on validated domain or ledger data.
- Reporting should not mutate persisted records.
- Reporting should not embed CLI-only formatting concerns.

## Current Project Status

Phase: Phase 2

Completed:

- Typer CLI scaffold.
- Rich formatting.
- Pydantic models.
- `JournalLine` and line-based `JournalEntry` validation.
- Computed debit and credit totals.
- Balance checks for journal entries.
- Validation tests for the journal model and journal rules.

Partially Completed:

- CLI command structure. The `journal` group exists, but there are no operational subcommands yet.
- Account model test coverage. The model exists, but the test file is still a placeholder.

Not Yet Implemented:

- Ledger posting.
- Trial Balance.
- Persistence layer.
- Repository layer.
- Reporting layer.

## Target Folder Structure

The long-term repository layout should preserve the current separation of concerns while adding explicit layers for
repositories, storage, and reports.

```text
src/pyledger/
├── __init__.py
├── main.py
│
├── cli/
│   ├── __init__.py
│   ├── app.py
│   └── commands/
│       ├── __init__.py
│       └── journal_command.py
│
├── core/
│   ├── __init__.py
│   ├── errors.py          <- domain error codes and messages
│   ├── helpers.py         <- posting dates and journal numbering
│   ├── models/
│   │   ├── __init__.py
│   │   ├── account.py     <- Account, AccountCategory
│   │   └── journal.py     <- JournalEntry, JournalLine
│   ├── rules/
│   │   ├── __init__.py
│   │   └── journal_rules.py  <- balance invariants, amount/name validators
│   └── services/
│       └── __init__.py    <- placeholder for posting logic
│
├── repositories/
│   └── __init__.py        <- placeholder
│
├── storage/
│   └── __init__.py        <- placeholder
│
├── reports/
│   └── __init__.py        <- placeholder
│
└── utils/
    ├── __init__.py
    ├── console.py          <- Rich console and theme setup
    ├── constants.py        <- display-only formatting strings
    └── formatter.py        <- Rich tables, panels, validation rendering

tests/
├── __init__.py
├── conftest.py
├── helpers.py
├── core/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── test_account_model.py
│   │   └── test_journal_model.py
│   ├── rules/
│   │   ├── __init__.py
│   │   └── test_journal_rules.py
├── cli/
│   └── __init__.py
├── reports/
│   └── __init__.py
└── utils/
    ├── __init__.py
    └── test_formatter.py
```

This structure keeps the accounting rules at the center and lets the application evolve in controlled layers:

- `core/` answers what the business rules are.
- `repositories/` defines how the application asks for data.
- `storage/` defines where the data actually lives.
- `reports/` defines how validated accounting data is summarized.
- `cli/` defines how users interact with the system.
- `utils/` supports the user interface and shared helpers.

## Design Principles

PyLedger architecture should continue to follow these rules:

- Keep business logic independent of Typer and Rich.
- Keep the CLI thin.
- Keep storage behind interfaces.
- Keep reporting separate from persistence.
- Prefer explicit data flow over hidden state.
- Validate accounting rules as early as possible.
- Preserve double-entry integrity at every boundary.

## Summary

The current codebase is a compact CLI bookkeeping prototype with a line-based journal model, validation helpers, and
well-defined presentation helpers. The next major architectural steps are to introduce repository abstractions, add
real storage implementations, and build reporting modules that can generate ledger and trial balance outputs from
validated accounting data.
