# PyLedger

PyLedger is a Python CLI bookkeeping application built around double-entry accounting. It focuses on domain modeling,
validation, service-layer workflows, and a small MongoDB infrastructure layer rather than reporting. The codebase is
intentionally structured as an educational, architecture-first prototype for exploring how bookkeeping rules can be
enforced in Python.

## Overview

PyLedger exists to model the core mechanics of a bookkeeping system in a small, inspectable codebase. It captures the
chart of accounts, journal lines, journal entries, and ledger postings that sit at the heart of double-entry
accounting.

The project is useful as a reference for:

- understanding how accounting rules can be represented as validated domain models,
- separating user interaction from business rules,
- keeping service orchestration independent of terminal presentation,
- and demonstrating how Clean Architecture boundaries can be applied in a Python CLI project.

The current implementation is deliberately limited. It validates account, journal, and posting data; provides service
workflows for account, journal, and posting operations; and includes a MongoDB account repository plus the related
connection and error-translation helpers.

## Current Features

### Implemented

- Chart of accounts domain model with case-insensitive account-name lookup and unique code/name validation.
- Account domain model with normalized names and category-derived normal balance.
- Account service workflows for create, update, lookup, list, resolve, and delete.
- JournalLine validation for normalized account names and debit/credit exclusivity.
- JournalEntry validation for positive journal numbers, supported posting dates, minimum line count, and balanced
  totals.
- Journal DTOs for service input and output contracts.
- Journal service workflows for create, get, and list, including journal-number allocation.
- Immutable LedgerPosting model with the same single-side posting rule.
- Async repository contracts for accounts, journals, and postings.
- MongoDB connection helpers, shared Mongo execution/error translation, timestamped documents, and concrete
  MongoDB account and journal repositories.
- Shared validation helpers for account-name normalization and line-amount checks.
- Shared error model and Pydantic error translation helpers.
- Rich journal entry and journal list formatting helpers.
- Typer application bootstrap with a `journal` command group scaffold.
- Domain and service tests for account, journal, posting, and shared error behavior.
- MongoDB infrastructure tests for the connection lifecycle and the MongoDB account and journal repositories.

### Partial or Scaffolded

- CLI error formatting and message catalog modules exist, but no live command path uses them yet.
- `src/pyledger/modules/journal/rule.py` is an empty scaffold.
- `src/pyledger/modules/posting/rule.py` is an empty scaffold.
- The CLI has no operational account, journal, or posting commands beyond the root app and journal group scaffold.

### Planned

- Concrete storage adapter for posting workflows.
- Trial balance and reporting support.
- Operational CLI workflows for accounts, journals, and postings.
- Import/export and integration surfaces.

## Architecture

PyLedger follows Clean Architecture ideas in a lightweight form:

- Domain models own the accounting rules.
- DTOs define service boundaries.
- Services orchestrate validation and repository access.
- Repository contracts define persistence boundaries.
- Shared error types and validation helpers stay independent of the CLI.

The main validation boundary is in the feature modules. Pydantic models enforce structural rules, shared validation
helpers normalize common inputs, and services perform cross-record checks such as account existence and journal-number
allocation.

```text
CLI
 ↓
Services
 ↓
Domain Models
 ↓
Repository Contracts
↓
Storage Adapters (remaining)
```

## Repository Structure

```text
.
├── AGENTS.md
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PROJECT_CONTEXT.md
│   └── ROADMAP.md
├── pyproject.toml
├── src/
│   └── pyledger/
│       ├── conftest.py
│       ├── main.py
│       ├── cli/
│       │   ├── app.py
│       │   ├── console.py
│       │   ├── commands/
│       │   │   └── journal_cmd.py
│       │   ├── constants/
│       │   │   └── errors.py
│       │   ├── formatters/
│       │   │   ├── base.py
│       │   │   ├── error_fmt.py
│       │   │   └── journal_fmt.py
│       │   └── theme/
│       │       ├── detection.py
│       │       └── styles.py
│       ├── infrastructure/
│       │   └── mongo/
│       │       ├── account/
│       │       │   ├── document.py
│       │       │   ├── repository.py
│       │       │   └── tests/
│       │       ├── journal/
│       │       │   ├── document.py
│       │       │   ├── repository.py
│       │       │   └── tests/
│       │       ├── connection.py
│       │       ├── error_translation.py
│       │       ├── shared/
│       │       │   ├── document.py
│       │       │   ├── repository.py
│       │       │   └── tests/
│       │       └── tests/
│       ├── modules/
│       │   ├── account/
│       │   │   ├── dtos.py
│       │   │   ├── repo.py
│       │   │   ├── service.py
│       │   │   ├── schemas/
│       │   │   │   ├── account.py
│       │   │   │   └── chart.py
│       │   │   └── tests/
│       │   ├── journal/
│       │   │   ├── dtos.py
│       │   │   ├── repo.py
│       │   │   ├── service.py
│       │   │   ├── schemas/
│       │   │   │   ├── journal.py
│       │   │   │   └── line.py
│       │   │   └── tests/
│       │   └── posting/
│       │       ├── dtos.py
│       │       ├── repo.py
│       │       ├── rule.py
│       │       ├── service.py
│       │       ├── schemas/
│       │       │   └── ledger_posting.py
│       │       └── tests/
│       └── shared/
│           ├── rule.py
│           ├── util.py
│           ├── errors/
│           │   ├── codes.py
│           │   ├── errors.py
│           │   └── translators.py
│           └── tests/
└── tests/
    ├── factories/
    ├── fakes/
    └── fixtures/
```

## Technology Stack

- Python 3.14+ - modern typing features and the current runtime target.
- UV - dependency and environment management.
- Typer - command-line application framework for the CLI entry point and command groups.
- Rich - terminal rendering for formatted journal output and styled panels.
- Pydantic v2 - domain and DTO validation with structured error reporting.
- Pytest - test runner for domain, service, and shared utility tests.
- Ruff - linting and formatting.

## Development Setup

```bash
uv sync --dev
```

```bash
pytest -m unit
```

```bash
pytest -m integration
```

```bash
ruff check
```

```bash
ruff format
```

```bash
ty check
```

## Environment Configuration

Copy the example environment files and customize them as needed:

```bash
cp .env.example .env
cp .env.test.example .env.test
```

- `.env` contains settings for local development.
- `.env.test` contains settings used by the test suite.
- Test settings use nested environment variables such as `PYLEDGER_TEST_MONGO__URI` and `PYLEDGER_TEST_MONGO__DB`.
- The test database should be separate from the development database to avoid accidental data loss.

## Current Project Status

### Implemented

- Account domain model, chart-of-accounts model, DTOs, repository contract, and service workflows.
- Journal line and journal entry validation.
- Journal DTOs, repository contract, and service workflows.
- LedgerPosting model and posting service workflows.
- Shared validation helpers and shared error translation.
- MongoDB connection lifecycle helpers, error translation, timestamped documents, and concrete MongoDB account and
  journal repositories.
- Typed configuration layer with isolated test settings.
- Rich journal formatting helpers.
- Typer application bootstrap and journal command group scaffold.
- Account, journal, posting, and shared error tests.
- MongoDB connection and repository tests.

### Partial

- CLI error formatter and CLI error catalog modules.
- `modules/journal/rule.py`.
- `modules/posting/rule.py`.
- Concrete storage adapter for posting workflows.
- Operational CLI commands beyond the journal group scaffold.

### Planned

- Trial balance and reporting support.
- Operational account, journal, and posting CLI commands.
- Import/export and integration surfaces.

## Roadmap

The next milestones are to add a concrete posting storage adapter and wire operational account, journal, and posting
CLI workflows into the Typer app. After that, the project can move toward trial balance reporting, historical views,
and import/export support.

## Design Principles

- Double-entry accounting correctness: journal entries must balance and journal lines must carry exactly one side.
- Explicit validation: invalid data should fail at the domain boundary with structured errors.
- Type safety: Pydantic models and strict typing define the contracts between layers.
- Testability: services depend on repository interfaces, which makes them easy to fake in tests.
- Separation of concerns: CLI presentation, business logic, and persistence stay in separate layers.
- Future extensibility: repository contracts and DTO boundaries leave room for storage adapters and more workflows.

## Contributing

Keep changes focused and consistent with the existing architecture. Update or add tests when behavior changes, run the
project formatting and lint checks locally, and avoid documenting scaffolding as implemented behavior.

## License

No license file is present in the repository yet.
