# PyLedger Project Context

## Overview

PyLedger is a Python command-line bookkeeping application for double-entry accounting. The current repository is a
feature-oriented domain prototype with working account, journal, and posting services; validated journal and posting
models; journal and posting DTOs; journal and posting repository contracts; shared error translation; Rich-based
journal rendering; and concrete MongoDB account, journal, and posting repositories plus their supporting
infrastructure. Reporting and operational CLI commands are not implemented yet.

## Repository Shape

- `src/pyledger/main.py` boots the Typer application. The file contains only the active entry point and invokes `app()`.
- `src/pyledger/cli/` contains the Typer app, Rich console setup, themes, formatters, CLI constants, and a journal
  command scaffold.
- `src/pyledger/modules/account/` contains the active account domain, DTOs, async repository contract, service layer,
  and tests.
- `src/pyledger/modules/journal/` contains journal schemas, DTOs, the async repository contract, a workflow service,
  and schema/service tests.
- `src/pyledger/modules/posting/` contains the immutable posting schema, the `PostingViewModel` DTO, the async
  repository contract, the implemented posting service, schema/DTO/service tests, and the empty `rule.py` scaffold.
- `src/pyledger/infrastructure/mongo/` contains the MongoDB connection helpers, shared executor and error-translation
  utilities, the MongoDB account, journal, and posting documents and repositories, and infrastructure tests.
- `src/pyledger/infrastructure/mongo/posting/` contains the MongoDB posting document, repository implementation, and
  repository tests.
- `src/pyledger/shared/` contains reusable validation helpers, utility code, and the shared error model.
- `src/pyledger/conftest.py` registers the shared pytest fixture plugins.
- `tests/` contains shared fixtures, factories, and fakes, not application test cases.
- Module-local tests live under `src/pyledger/modules/**/tests/`.
- Shared error tests live under `src/pyledger/shared/errors/tests/`.
- Shared rule tests live under `src/pyledger/shared/tests/`.
- MongoDB infrastructure tests live under `src/pyledger/infrastructure/mongo/**/tests/`.

## Current State

- `Account` enforces code, name, and category validation and derives `normal_balance` from category.
- `ChartOfAccounts` enforces unique codes and unique canonical names, and resolves accounts with `get_by_code()` and
  `get_by_name()`.
- `JournalLine` enforces account normalization and debit/credit exclusivity.
- `JournalEntry` enforces minimum line count, positive journal number, supported posting dates, and balanced totals.
- `JournalRepo` defines async save, lookup, list, and journal-number allocation methods.
- `pyledger.infrastructure.mongo.journal` exposes `JournalDocument`, `JournalLineSubDocument`, and `MongoJournalRepo`.
- `pyledger.infrastructure.mongo.posting` exposes `PostingDocument` and `MongoPostingRepo`.
- `JournalService` validates account references, allocates journal numbers, persists entries, and returns view models.
- `LedgerPosting` is an immutable derived record with the same single-side amount rule.
- `AccountService` is complete end to end for create, update, lookup, list, resolve, and delete workflows.
- `MongoAccountRepo` is the concrete account repository adapter.
- `MongoJournalRepo` is the concrete journal repository adapter and maps duplicate journal-number collisions to
  `ErrorCode.DUPLICATE_JOURNAL_NUMBER`.
- `MongoPostingRepo` is the concrete posting repository adapter and stores postings in MongoDB with case-insensitive
  account lookup support and deterministic per-journal ordering.
- `JournalRepo` and `PostingRepo` define async persistence and lookup methods, and concrete MongoDB adapters exist for
  the account, journal, and posting repository contracts.
- `PostingService` exposes `post_journal_entry()`, `get_postings_by_account()`, and `get_postings_by_journal_number()`
  for journal-to-posting workflows, but it is not yet wired into the CLI.
- `cli/formatters/journal_fmt.py` renders journal view models.
- `cli/formatters/error_fmt.py` and `cli/constants/errors.py` exist and import, but no command currently uses them.
- There is no trial balance or reporting pipeline.
- `pyledger.config` provides `Settings`, `TestSettings`, `MongoSettings`, and a cached `get_settings()` accessor. Settings load from `PYLEDGER_`-prefixed environment variables and an optional `.env` file. `TestSettings` uses `PYLEDGER_TEST_` and `.env.test`.
- `pyledger.infrastructure.mongo` provides `connect()`, `disconnect()`, and `MongoConnection` for MongoDB lifecycle
  management. `pyledger.infrastructure.mongo.shared` exposes `MongoExecutor` and `TimestampedDocument`,
  `pyledger.infrastructure.mongo.account` exposes `AccountDocument` and `MongoAccountRepo`,
  `pyledger.infrastructure.mongo.journal` exposes `JournalDocument`, `JournalLineSubDocument`, and `MongoJournalRepo`,
  and `pyledger.infrastructure.mongo.posting` exposes `PostingDocument` and `MongoPostingRepo`.

## Accounting Model

PyLedger follows standard double-entry accounting.

```text
Journal Entry -> Ledger Posting
```

Both stages in the diagram are currently implemented as live workflows in the service layer. There is still no trial
balance pipeline or downstream reporting layer.

## Domain Models

### Account

- Fields: `code`, `name`, `category`, and computed `normal_balance`.
- `code` is limited to 1 to 20 characters and must match the account code pattern.
- `name` is normalized by `clean_account_name()` and must be 2 to 150 characters long.
- `category` is one of `ASSET`, `LIABILITY`, `EQUITY`, `REVENUE`, `EXPENSE`, `DIVIDEND`, or `DRAWING`.
- `normal_balance` is derived from the category and is not stored independently.
- Account aliases are not implemented.

### ChartOfAccounts

- Enforces unique account codes.
- Enforces unique canonical names case-insensitively.
- Resolves by code with `get_by_code()`.
- Resolves by canonical name with `get_by_name()`.
- Does not expose a `resolve()` method.
- Does not implement aliases.

### JournalLine

- Fields: `account`, `debit_amount`, and `credit_amount`.
- `account` is normalized with `clean_account_name()`.
- A line must carry either a debit amount or a credit amount, not both and not neither.
- Negative amounts are rejected by the schema.

### JournalEntry

- Fields: `journal_number`, `posting_date`, `lines`, and optional `description`.
- `journal_number` must be positive.
- `posting_date` must be later than `2020-01-01` and must not be in the future.
- `lines` must contain at least two `JournalLine` records.
- `total_debits`, `total_credits`, and `is_balanced` are computed fields.
- Unbalanced entries are rejected.

### LedgerPosting

- Fields: `account`, `debit_amount`, `credit_amount`, `journal_number`, and `posting_date`.
- `LedgerPosting` is frozen after creation.
- `account` is normalized with `clean_account_name()`.
- `journal_number` must be positive.
- `posting_date` must be later than `2020-01-01` and must not be in the future.
- `is_debit` is a derived boolean helper.

## DTOs

- `modules/account/dtos.py` defines `CreateAccountInput`, `UpdateAccountInput`, `AccountViewModel`, and
  `ChartOfAccountsViewModel`.
- `modules/journal/dtos.py` defines `JournalLineInput`, `CreateJournalInput`, `JournalLineViewModel`, and
  `JournalViewModel`.
- `CreateJournalInput` does not include `journal_number`; `JournalService` assigns it through the repository.
- `modules/posting/dtos.py` defines `PostingViewModel` with a computed `is_debit` field. There is no posting input DTO because postings are derived from
  validated journal entries.

## Service Layer And CLI

- `AccountService` exposes `create_account()`, `update_account()`, `get_account()`, `get_chart()`,
  `resolve_account()`, `list_accounts()`, and `delete_account()`.
- `AccountService` raises `AppError` for business conflicts and `ValidationAppError` for domain validation failures.
- `AccountService.delete_account()` currently checks existence only; posting-history safeguards are not implemented.
- `JournalService` exposes `create_journal_entry()`, `get_journal_entry()`, and `list_journal_entries()`.
- `JournalService` validates account references through `AccountService`, allocates journal numbers via `JournalRepo`,
  constructs `JournalEntry`, and persists or returns view models.
- `PostingService` exposes `post_journal_entry()`, `get_postings_by_account()`, and `get_postings_by_journal_number()`. It derives postings from `JournalViewModel` instances returned by `JournalService` and persists them via `PostingRepo`.
- The CLI currently registers the root app and a `journal` command group, but there are no operational subcommands.
- The journal formatter can render `JournalViewModel` instances, but no command currently feeds it data.
- The error formatter and CLI error catalog are present, but no live command path uses them yet.

## Error System

- `src/pyledger/shared/errors/` defines `ErrorCode`, `AppError`, `ValidationAppError`, `FieldViolation`, and the
  Pydantic translation helpers.
- `pydantic_error()` is used by schema validators to raise domain error codes through Pydantic.
- `get_field_violations()` converts Pydantic validation output into stable `FieldViolation` records.
- `AppError.storage_unavailable()` and `AppError.storage_timeout()` translate MongoDB connectivity failures into
  structured application errors.
- The CLI owns the user-facing message catalog in `cli/constants/errors.py` and the render path in
  `cli/formatters/error_fmt.py`.
- The CLI error copy for invalid account names and unknown accounts is currently stale; it still mentions abbreviations
  and aliases even though alias support is not implemented.

## Testing

- Pytest is configured to collect tests from `tests/` and `src/pyledger/`.
- Root-level `tests/` contains `fixtures/`, `factories/`, and `fakes/`.
- `src/pyledger/conftest.py` registers the fixture modules as pytest plugins.
- `tests/fakes/account_repo.py`, `tests/fakes/journal_repo.py`, and `tests/fakes/posting_repo.py` provide in-memory
  repository fakes for service tests.
- The journal fake issues journal numbers sequentially and stores entries in memory.
- Feature tests live beside the feature code under `src/pyledger/modules/**/tests/`.
- Shared error tests live under `src/pyledger/shared/errors/tests/`.
- Shared rule tests live under `src/pyledger/shared/tests/`.
- Current automated coverage is concentrated on domain models, shared validation helpers, shared error translation,
  `AccountService`, `JournalService`, `PostingService`, and MongoDB infrastructure behavior.
- Journal schema tests cover `JournalLine` and `JournalEntry`.
- Journal DTO tests cover `JournalLineInput`, `CreateJournalInput`, `JournalLineViewModel`, and `JournalViewModel`.
- Journal service tests cover create, get, list, account validation, domain validation, and journal-number allocation.
- Posting schema tests cover `LedgerPosting`.
- Posting DTO tests cover `PostingViewModel`.
- Posting service tests cover journal-to-posting derivation, duplicate-posting prevention, and posting retrieval.
- Posting repository tests cover `MongoPostingRepo` mapping, ordering, and persistence behavior.
- `tests/factories/posting.py` provides posting service and domain-object factories for posting tests.
- `tests/fixtures/posting.py` provides posting fixtures and a `MongoPostingRepo` fixture for repository tests.
- MongoDB connection tests live under `src/pyledger/infrastructure/mongo/tests/`.
- MongoDB account repository tests live under `src/pyledger/infrastructure/mongo/account/tests/`.
- MongoDB journal repository tests live under `src/pyledger/infrastructure/mongo/journal/tests/`.
- MongoDB posting repository tests live under `src/pyledger/infrastructure/mongo/posting/tests/`.
- `tests/fixtures/settings.py` provides the session-scoped `test_settings` fixture and the `isolate_settings_cache`
  autouse fixture that clears the `get_settings` LRU cache before and after every test.
- `tests/fixtures/journal.py` provides journal domain fixtures, a `MongoJournalRepo` fixture, and a document-settings
  stub for unit tests that construct `JournalDocument` instances without Beanie initialization.
- `tests/fixtures/mongo.py` provides `mongo_connection`, `beanie_init`, and `clean_db` fixtures for Mongo-backed
  integration tests. It also registers `AccountDocument`, `JournalDocument`, and `PostingDocument` with Beanie and
  truncates the collections used by MongoDB integration tests.
- There are no reporting or CLI workflow tests yet.
- Settings tests live under `src/pyledger/config/tests/`.
- Posting service tests cover `post_journal_entry`, `get_postings_by_account`, and `get_postings_by_journal_number` workflows including duplicate-posting detection.

## Known Issues

- Alias support is not implemented anywhere in the active code path.
- The CLI invalid-account-name and unknown-account messages are out of sync with the actual account-name validator and
  chart lookup behavior.
- `MongoPostingRepo.save_many()` uses a batch `insert_many()` call without transaction support, so a mid-batch
  interruption can partially persist a journal's postings and concurrent posting attempts can still race.
- There are no operational CLI commands yet.

## Long-Term Direction

- Harden posting persistence for stronger write-consistency guarantees if needed.
- Wire posting, journal, and account workflows into the CLI.
- Build trial balance and reporting support from validated data.
- Add import/export and integration surfaces once the core bookkeeping workflow is stable.
