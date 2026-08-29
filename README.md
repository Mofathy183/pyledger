# Trutina

Trutina is a Python CLI bookkeeping application built around double-entry accounting. It combines validated domain
modeling, service-layer workflows, a MongoDB infrastructure layer, and a fully implemented Typer/Rich CLI, rather
than reporting. The codebase is intentionally structured as an educational, architecture-first project for exploring
how bookkeeping rules can be enforced in Python and exposed through a clean, layered command-line interface.

## Overview

Trutina exists to model the core mechanics of a bookkeeping system in a small, inspectable codebase. It captures the
chart of accounts, journal lines, journal entries, and ledger postings that sit at the heart of double-entry
accounting.

The project is useful as a reference for:

- understanding how accounting rules can be represented as validated domain models,
- separating user interaction from business rules,
- keeping service orchestration independent of terminal presentation,
- and demonstrating how Clean Architecture boundaries can be applied in a Python CLI project.

The current implementation validates account, journal, and posting data; provides service workflows for account,
journal, and posting operations; includes MongoDB account, journal, and posting repositories plus the related
connection and error-translation helpers; and exposes all of it through a complete `account`/`journal`/`posting`
CLI built on Typer and Rich. Reporting (trial balance, historical views) is the main area still deliberately out
of scope — see `src/trutina/cli/README.md` for full CLI architecture and `docs/ROADMAP.md` for what's next.

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
- Posting DTOs and posting service workflows for journal-to-posting derivation, duplicate-posting prevention, and
  retrieval by account or journal number.
- Async repository contracts for accounts, journals, and postings.
- MongoDB connection helpers, shared Mongo execution/error translation, timestamped documents, and concrete
  MongoDB account, journal, and posting repositories.
- Shared validation helpers for account-name normalization and line-amount checks.
- Shared error model and Pydantic error translation helpers.
- A complete, feature-oriented CLI (`account`, `journal`, `posting` Typer command groups) with its own composition
  root (`CliContext`, `CliState`), CLI-flag and interactive-prompt input paths, Rich-based formatters for every
  command, and a shared error boundary that renders domain and validation failures as terminal panels. See
  `src/trutina/cli/README.md` for the full CLI architecture.
- Domain and service tests for account, journal, posting, and shared error behavior.
- CLI unit and integration tests for all three command groups, plus composition-root tests.
- MongoDB infrastructure tests for the connection lifecycle and the MongoDB account, journal, and posting repositories.

### Partial or Scaffolded

- `src/trutina/modules/journal/rule.py` is an empty scaffold.
- `src/trutina/modules/posting/rule.py` is an empty scaffold.

### Planned

- Trial balance and reporting support.
- Import/export and integration surfaces.

## Architecture

Trutina follows Clean Architecture ideas in a lightweight form:

- Domain models own the accounting rules.
- DTOs define service boundaries.
- Services orchestrate validation and repository access.
- Repository contracts define persistence boundaries.
- Shared error types and validation helpers stay independent of the CLI.
- The CLI is a thin, feature-oriented presentation layer over the service layer, with its own internal layering
  (command → parser/prompt → handler → formatter) documented in `src/trutina/cli/README.md`.

The main validation boundary is in the feature modules. Pydantic models enforce structural rules, shared validation
helpers normalize common inputs, and services perform cross-record checks such as account existence and journal-number
allocation.

```text
User
 ↓
Typer Command (cli/features/<feature>/command.py)
 ↓
Parser / Prompt
 ↓
Handler
 ↓
Service
 ↓
Domain Models
 ↓
Repository Contracts
 ↓
Storage Adapters (MongoDB)
```

MongoDB storage adapters are implemented for accounts, journals, and postings. The CLI bridges its synchronous
Typer/Click dispatch onto this async stack through a single `BlockingPortal`, owned for the life of the process by
`main.py`. Full CLI architecture — the composition root, async execution model, error handling, and layer-by-layer
dependency rules — is documented in `src/trutina/cli/README.md`.

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
│   └── trutina/
│       ├── conftest.py
│       ├── main.py
│       ├── cli/
│       │   ├── app.py
│       │   ├── bootstrap.py
│       │   ├── context.py
│       │   ├── state.py
│       │   ├── features/
│       │   │   ├── account/
│       │   │   │   ├── command.py
│       │   │   │   ├── parser.py
│       │   │   │   ├── prompt.py
│       │   │   │   ├── handler.py
│       │   │   │   ├── formatter.py
│       │   │   │   └── tests/
│       │   │   ├── journal/
│       │   │   │   ├── command.py
│       │   │   │   ├── parser.py
│       │   │   │   ├── prompt.py
│       │   │   │   ├── handler.py
│       │   │   │   ├── formatter.py
│       │   │   │   └── tests/
│       │   │   └── posting/
│       │   │       ├── command.py
│       │   │       ├── parser.py
│       │   │       ├── prompt.py
│       │   │       ├── handler.py
│       │   │       ├── formatter.py
│       │   │       └── tests/
│       │   ├── shared/
│       │   │   ├── error_boundary.py
│       │   │   ├── interaction/
│       │   │   │   └── prompt.py
│       │   │   ├── ui/
│       │   │   │   ├── console.py
│       │   │   │   ├── widgets.py
│       │   │   │   └── theme/
│       │   │   │       ├── detection.py
│       │   │   │       └── styles.py
│       │   │   ├── errors/
│       │   │   │   ├── errors.py
│       │   │   │   └── hint.py
│       │   │   └── formatters/
│       │   │       └── error.py
│       │   └── tests/
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
│       │       ├── posting/
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

See `src/trutina/cli/README.md` for a full description of every file under `cli/`.

## Technology Stack

- Python 3.14+ - modern typing features and the current runtime target.
- UV - dependency and environment management.
- Typer - command-line application framework for the CLI entry point and the `account`/`journal`/`posting`
- Rich - terminal rendering for formatted account, journal, and posting output, styled panels, and error rendering.
- Pydantic v2 - domain and DTO validation with structured error reporting.
- Pytest - test runner for domain, service, and shared utility tests.
- Ruff - linting and formatting.
- AnyIO - bridges the CLI's synchronous Typer dispatch onto the async service/repository layer via a single
  `BlockingPortal`.

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
- Test settings use nested environment variables such as `TRUTINA_TEST_MONGO__URI` and `TRUTINA_TEST_MONGO__DB`.
- The test database should be separate from the development database to avoid accidental data loss.

## Current Project Status

### Implemented

- Account domain model, chart-of-accounts model, DTOs, repository contract, and service workflows.
- Journal line and journal entry validation.
- Journal DTOs, repository contract, and service workflows.
- LedgerPosting model and posting service workflows.
- Shared validation helpers and shared error translation.
- MongoDB connection lifecycle helpers, error translation, timestamped documents, and concrete MongoDB account,
  journal, and posting repositories.
- Typed configuration layer with isolated test settings.
- A complete CLI: Typer application bootstrap, composition root (`CliContext`/`CliState`), and fully wired
  `account`, `journal`, and `posting` command groups with Rich-based formatting and a shared error-rendering
  boundary.
- Account, journal, posting, and shared error tests.
- CLI unit and integration tests for all three feature groups, plus composition-root tests.
- MongoDB connection and repository tests.

### Partial

- `modules/journal/rule.py`.
- `modules/posting/rule.py`.

### Planned

- Trial balance and reporting support.
- Import/export and integration surfaces.

## Roadmap

With the CLI now complete for account, journal, and posting workflows, the next milestones move toward trial
balance reporting, historical views, and import/export support. See `docs/ROADMAP.md` for the full breakdown and
`src/trutina/cli/README.md`'s "Future Work" section for CLI-specific next steps (e.g. additional command groups
once reporting exists, shell completion, richer interactive workflows).

## Design Principles

- Double-entry accounting correctness: journal entries must balance and journal lines must carry exactly one side.
- Explicit validation: invalid data should fail at the domain boundary with structured errors.
- Type safety: Pydantic models and strict typing define the contracts between layers.
- Testability: services depend on repository interfaces, which makes them easy to fake in tests.
- Separation of concerns: CLI presentation, business logic, and persistence stay in separate layers — the CLI
  itself is further layered internally (command → parser/prompt → handler → formatter), documented in
  `src/trutina/cli/README.md`.
- Future extensibility: repository contracts and DTO boundaries leave room for storage adapters and more workflows.

## Contributing

Keep changes focused and consistent with the existing architecture. Update or add tests when behavior changes, run the
project formatting and lint checks locally, and avoid documenting scaffolding as implemented behavior.

## License

No license file is present in the repository yet.
