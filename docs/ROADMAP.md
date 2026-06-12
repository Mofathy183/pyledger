# PyLedger Roadmap

## Purpose

This roadmap describes a realistic path for PyLedger from the current CLI prototype to a more complete bookkeeping
system. The ordering is intentional: accounting correctness comes first, then persistence, then richer reporting and
integration surfaces.

The project should not move to storage or APIs before the accounting core is dependable.

## Roadmap Principles

- Build the accounting model before building persistence.
- Keep the domain independent of the CLI and terminal formatting.
- Add features only when the underlying bookkeeping flow is stable.
- Prefer small, testable increments over broad rewrites.
- Treat balancing rules and account behavior as non-negotiable.

## Current Status

- Completed: Phase 0 and Phase 1.
- Partially Completed: Phase 2, including the compound journal-entry refactor.
- Not Started: Phase 3 through Phase 8.

## Phase 0: Project Bootstrap

### Goal

Establish the project foundation, development tooling, and repository structure required to implement and validate the
accounting domain safely and consistently.

### Status

Completed.

### Features

* Python project initialization with UV.
* Source-layout package structure.
* Ruff configuration for linting and formatting.
* pytest configuration and testing conventions.
* Typer application bootstrap.
* Rich console integration.
* Initial project documentation.
* Development workflow and repository standards.

### Deliverables

* Configured `pyproject.toml`.
* Working `src/` package structure.
* CLI entrypoint and application bootstrap.
* Ruff and development tooling configuration.
* Initial documentation set:

    * `AGENTS.md`
    * `PROJECT_CONTEXT.md`
    * `ARCHITECTURE.md`
    * `ROADMAP.md`
* Reproducible local development environment.

### Dependencies

None.

### Definition of Done

* The project installs successfully through UV.
* The CLI application can be executed from the command line.
* Linting and formatting tools are configured.
* The repository structure follows the documented architecture.
* Documentation exists for project context, architecture, and roadmap.
* The project is ready for implementation of the accounting domain.

### Notes

Phase 0 focuses exclusively on project setup and development infrastructure. No accounting workflows, posting logic,
ledger behavior, or reporting features are required at this stage.

## Phase 1: Harden the Core Journal Model

### Goal

Make the journal-entry domain reliable, explicit, and fully covered by business-rule tests.

### Status

Completed.

### Features

- Balanced journal-entry validation.
- Strict account-name validation.
- Negative amount rejection.
- Posting-date validation.
- Journal number generation behavior.
- Clear domain error messages and validation failures.

### Deliverables

- Refined `JournalEntry` and related core models.
- Business-rule tests for the domain layer.
- Consistent validation behavior for CLI and future internal callers.
- Clean separation between domain logic and presentation code.

### Dependencies

- Existing Pydantic model structure.
- Test framework and project test conventions.
- Agreement on core account terminology and validation rules.

### Definition of Done

- Journal entries cannot be created in an invalid accounting state.
- Validation rules are covered by automated tests.
- Domain behavior is usable without Typer or Rich.
- Error cases are deterministic and documented through tests.

## Phase 2: Add Account Structure and Posting Rules

### Goal

Introduce explicit account behavior so PyLedger can reason about debit-normal and credit-normal accounts beyond a single
journal entry.

### Status

Partially Completed.

### Features

- Account catalog model.
- Account categories and normal-balance rules.
- Posting logic that maps journal entries to account movements.
- Balance accumulation per account.
- Validation that posting preserves accounting integrity.

### Deliverables

- Core account models with clear responsibilities.
- Ledger posting logic in the domain layer.
- Tests for normal-balance handling and posting behavior.
- A defined internal workflow from journal entry to posted ledger data.

### Dependencies

- Phase 1 domain validation.
- Stable account type definitions.
- Clear rules for how postings are represented internally.

### Definition of Done

- The system can transform a balanced journal entry into account-level postings.
- Account balances behave correctly for all supported account types.
- Posting logic is tested independently of the CLI.
- No CLI or storage code is required to validate posting behavior.

## Phase 2: Compound Journal Entries

### Goal

Replace the current two-account journal model with a multi-line journal system.

### Status

Partially Completed.

### Tasks

- Completed: Create `JournalLine` model.
- Completed: Refactor `JournalEntry` to contain a collection of `JournalLine` records.
- Completed: Implement debit and credit aggregation validation.
- Not Started: Update CLI commands to support line-based entry creation.
- Completed: Add tests for compound transactions.

### Definition of Done

- `JournalEntry` supports any number of lines.
- Validation ensures total debits equal total credits.
- Existing functionality continues to work.

## Phase 3: Build Trial Balance Reporting

### Goal

Add the first complete accounting report so the application can verify that posted ledger activity still balances.

### Status

Not Started.

### Features

- Trial balance calculation from posted account data.
- Totals by account and by balance type.
- Detection of out-of-balance conditions.
- Basic summary output for terminal use.

### Deliverables

- Reporting logic for trial balance generation.
- Tests proving trial-balance equality when entries are valid.
- Tests proving failure behavior when ledger data is inconsistent.
- CLI-accessible trial balance output, if appropriate.

### Dependencies

- Phase 2 posting logic.
- A stable representation of ledger/account balances.
- Agreement on report formatting and fields.

### Definition of Done

- A valid set of postings can produce a correct trial balance.
- Trial balance output clearly exposes imbalances.
- Report logic is separate from persistence and independent of the CLI layer.

## Phase 4: Expand CLI Workflows

### Goal

Turn the CLI into a practical bookkeeping interface for creating, reviewing, and checking accounting data.

### Status

Not Started.

### Features

- Commands for creating journal entries.
- Commands for listing or previewing journal entries.
- Commands for viewing posted account activity.
- Commands for generating trial balance output.
- Better terminal error handling and user feedback.

### Deliverables

- Thin Typer commands wired to core accounting services.
- Consistent Rich-based terminal output.
- User-facing command help and examples.
- CLI tests for command behavior and output formatting.

### Dependencies

- Phase 1 validation.
- Phase 2 posting logic.
- Phase 3 trial balance reporting.

### Definition of Done

- A user can create and inspect accounting records from the CLI.
- The CLI delegates business logic rather than reimplementing it.
- Command output is readable, consistent, and tested.

## Phase 5: Introduce Repository Abstractions

### Goal

Define stable data-access contracts so the application can persist bookkeeping data without binding the domain to a
storage technology.

### Status

Not Started.

### Features

- Repository interfaces for journal entries, accounts, and ledger records.
- Query methods for lookup by date, journal number, and account.
- Separation of read and write concerns where appropriate.
- Testable contracts for persistence-adjacent behavior.

### Deliverables

- Repository layer package and interfaces.
- Tests for repository expectations using fakes or in-memory implementations.
- Stable data-access boundaries for future storage code.

### Dependencies

- Phase 2 and Phase 3 domain/reporting behavior.
- Clear decisions about what data must be persisted and queried.

### Definition of Done

- The core domain can work against repository abstractions.
- No business logic depends on a concrete storage backend.
- Repository interfaces are stable enough to support multiple storage implementations.

## Phase 6: Add Persistent Storage

### Goal

Persist accounting data reliably so PyLedger can survive beyond in-memory or single-session usage.

### Status

Not Started.

### Features

- File-based persistence or SQLite-backed persistence.
- Serialization and deserialization of domain objects.
- Safe loading of existing data.
- Storage mappers that isolate schema details from business objects.

### Deliverables

- Concrete storage implementation(s).
- Migration or bootstrap strategy for initial data.
- Persistence tests covering save/load round trips.
- Data integrity checks around stored journal entries and postings.

### Dependencies

- Phase 5 repository abstractions.
- Stable domain models and report inputs.
- Agreement on the first supported storage backend.

### Definition of Done

- Accounting data can be saved and loaded without losing meaning.
- The domain remains storage-agnostic.
- Persistence changes do not require rewrites to core accounting logic.

## Phase 7: Improve Reporting and Historical Views

### Goal

Expand PyLedger from a verification tool into a useful bookkeeping system with readable historical reports.

### Status

Not Started.

### Features

- Ledger reports by account.
- Account history and balance views.
- Trial balance history.
- Summary views for period-based analysis.
- Export-ready reporting structures.

### Deliverables

- Reporting module set that consumes domain or persisted data.
- Tests for report calculations and grouping logic.
- CLI hooks for generating reports on demand.

### Dependencies

- Phase 3 trial balance logic.
- Phase 6 persistence.
- Stable account and ledger data structures.

### Definition of Done

- Users can inspect bookkeeping history, not just current entries.
- Reports are accurate, repeatable, and derived from validated data.
- Reporting code remains separate from storage and CLI formatting.

## Phase 8: Add Import/Export and Integration Surfaces

### Goal

Make PyLedger interoperable with external workflows once the accounting core is stable.

### Status

Not Started.

### Features

- CSV or structured import/export.
- Machine-readable output formats.
- Optional API surface or plugin-friendly extension points.
- Future integrations with downstream financial tools.

### Deliverables

- Import/export commands or modules.
- External-data validation rules.
- Documentation for supported interchange formats.

### Dependencies

- Phases 1 through 7.
- Stable persistence and report structures.
- Clear data contracts for external consumers.

### Definition of Done

- External data can be exchanged without compromising accounting correctness.
- Integration features do not bypass validation or posting rules.
- Exported data matches internal accounting semantics.

## Recommended Priority Order

If the project is being worked in sequence, the recommended order is:

1. Harden the core journal model.
2. Add account structure and posting rules.
3. Build trial balance reporting.
4. Expand the CLI workflows.
5. Introduce repository abstractions.
6. Add persistent storage.
7. Improve reporting and historical views.
8. Add import/export and integration surfaces.

This order keeps accounting functionality ahead of persistence and APIs, which reduces the risk of building a storage or
interface layer on top of unstable business logic.

## Success Criteria For The Project

PyLedger should be considered on track when:

- journal entries are always validated before they are accepted,
- posting logic preserves double-entry integrity,
- trial balance reporting is available and trustworthy,
- storage is isolated behind repository interfaces,
- the CLI remains thin and easy to extend,
- future features do not weaken the accounting model.
