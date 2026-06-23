# PyLedger Roadmap

## Purpose

This roadmap reflects the current implementation state of the repository and the remaining work needed to turn the
code into a complete bookkeeping application. The order is intentional: finish the domain and service boundaries
before adding storage, reporting, or integration layers.

## Roadmap Principles

- Keep accounting correctness ahead of persistence.
- Keep the domain independent of the CLI and Rich formatting.
- Add infrastructure only after the accounting model is stable.
- Prefer small, testable increments.
- Do not mark a phase complete unless the code exists in the repository and is coherent with the surrounding modules.

## Current Status

- Completed: project bootstrap, shared validation rules, shared error model, account model basics, chart-of-accounts
  basics, journal line validation, journal entry validation, journal DTOs, journal repository contract, journal
  service workflows, derived posting model, posting DTOs, posting repository contract, posting service workflows,
  posting service tests, Typer/Rich scaffolding, journal rendering, account service, and journal/posting domain schema
  tests.
- Partial: CLI error formatting, CLI error presentation constants, and CLI command wiring.
- Not started: concrete storage, trial balance reporting, historical reports, and import/export surfaces.
- Removed: alias support is not a tracked roadmap item in the current codebase.

## Phase 0: Project Bootstrap

### Status

Completed.

### Completed Work

- UV-based project setup.
- Source-layout package structure.
- Ruff configuration.
- Pytest configuration and fixtures.
- Ty configuration.
- Typer application bootstrap.
- Rich console and theme scaffolding.
- Initial project documentation.

## Phase 1: Shared Domain Infrastructure

### Status

Completed.

### Completed Work

- `clean_account_name()`.
- `account_lookup_key()`.
- `is_valid_line_amounts()`.
- `ErrorCode`.
- `AppError` and `ValidationAppError`.
- Pydantic-to-domain error translation helpers.
- Shared rule tests.

## Phase 2: Account Domain Basics

### Status

Completed.

### Completed Work

- `AccountCategory`.
- `Account`.
- `ChartOfAccounts`.
- Unique account-code validation.
- Unique canonical-name validation.
- Case-insensitive canonical name lookup.
- Direct code lookup.
- Account schema tests for the implemented behavior.

### Removed Items

- Alias support on `Account`.
- Alias-aware uniqueness checks in `ChartOfAccounts`.
- A `resolve()` method on `ChartOfAccounts`.
- Alias-oriented test expectations.

## Phase 3: Journal Domain Validation

### Status

Completed.

### Completed Work

- `JournalLine` validation.
- `JournalEntry` validation and computed totals.
- Balance enforcement.
- Future-date rejection.
- Minimum line-count validation.
- Journal domain schema tests.

## Phase 4: Posting Domain Model

### Status

Completed.

### Completed Work

- `LedgerPosting`.
- Frozen posting records.
- Single-side posting validation.
- `PostingViewModel`.
- `PostingRepo` contract.
- Posting-domain schema tests.
- Posting DTO tests.

## Phase 5: Service Layer Completion

### Status

Completed.

### Completed Work

- `AccountService`.
- `AccountRepo`.
- `JournalRepo`.
- `PostingRepo`.
- DTOs for account, journal, and posting workflows.
- Journal service create, get, and list workflows.
- `PostingService` journal-to-posting derivation, duplicate-posting prevention, and posting retrieval workflows.
- Journal and posting service tests.

## Phase 6: CLI Presentation Layer

### Status

Partial.

### Completed Work

- Root Typer application.
- `journal` command group scaffold.
- Rich console setup.
- Theme detection and style definitions.
- Journal entry formatter.
- CLI error catalog and error formatter modules.

### Partial Work

- Reconcile CLI error copy with the shared error model and active validators.
- Account commands.
- Journal entry commands.
- Posting inspection commands.
- Trial balance commands.
- CLI tests for user-facing behavior.

## Phase 7: Concrete Storage

### Status

Not started.

### Expected Scope

- Repository implementations.
- Serialization and deserialization.
- Safe loading and saving of accounts, journal entries, and postings.
- Storage-specific tests.

## Phase 8: Trial Balance and Reporting

### Status

Not started.

### Expected Scope

- Trial balance calculation.
- Account balance summaries.
- Historical report views.
- Future financial statement support.

## Phase 9: Import/Export and Integrations

### Status

Not started.

### Expected Scope

- CSV or structured import/export.
- Machine-readable output formats.
- External integration surfaces.

## Known Issues

- The CLI account-name error copy is still ahead of the validator wording and should be reconciled.
- `PostingService` is implemented, but it is not yet wired into the CLI.
- `modules/posting/rule.py` is still an empty scaffold.
- There are no storage-backed repositories, no operational CLI commands, and no reporting pipeline yet.

## Success Criteria

PyLedger should be considered on track when:

- journal entries are always validated before acceptance,
- journal numbering remains deterministic,
- posting derivation remains deterministic,
- repository contracts are stable,
- storage is isolated behind interfaces,
- CLI error rendering matches the shared error model,
- trial balance reporting is available,
- the CLI stays thin,
- future features do not weaken the accounting model.
