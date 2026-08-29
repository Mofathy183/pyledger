# trutina-core

The double-entry accounting domain for Trutina: validated domain models, service
workflows, and repository contracts for accounts, journal entries, and ledger postings.
No database driver, no HTTP framework, no CLI framework — this package is pure business
logic plus the interfaces storage adapters must satisfy.

## What This Package Is

`trutina-core` owns the answer to "what is a valid accounting transaction and what
happens when you post one." It is consumed by `apps/cli` and `apps/api`, and its
repository contracts are implemented by `trutina-infrastructure`. Core itself never
imports any of those three.

If you're deciding where a change belongs: if it's a rule about debits, credits,
account codes, or posting derivation, it belongs here. If it's about Mongo documents,
Typer commands, or HTTP routes, it doesn't.

## Why It Exists

Splitting the accounting domain into its own package — independent of storage and
presentation — means:

- The same domain rules back both the CLI and the API without duplication.
- Domain and service tests run in milliseconds with no database, using `Fake*Repo`
  implementations from the shared test tree.
- Storage can change (Mongo today, something else later) without touching a single
  validation rule.

See `CONTEXT.md` for the reasoning behind this split and the constraints that keep it
intact.

## Installation

Within the workspace:

```bash
uv sync --package trutina-core
```

`trutina-core` depends only on `trutina-shared` (validation helpers, the error
model). It has no dependency on `trutina-infrastructure`, `trutina-config`,
`trutina-cli`, or `trutina-api`.

## Package Layout

```text
packages/core/src/trutina/core/
├── account/
│   ├── dtos.py          # CreateAccountInput, UpdateAccountInput, AccountViewModel, ChartOfAccountsViewModel
│   ├── repo.py           # AccountRepo — abstract persistence contract
│   ├── service.py        # AccountService — create/update/get/list/resolve/delete
│   └── schemas/
│       ├── account.py    # Account, AccountCategory
│       └── chart.py      # ChartOfAccounts
├── journal/
│   ├── dtos.py           # CreateJournalInput, JournalLineInput, JournalViewModel, JournalLineViewModel
│   ├── repo.py            # JournalRepo — abstract persistence contract
│   ├── service.py         # JournalService — create/get/list
│   └── schemas/
│       ├── journal.py     # JournalEntry
│       └── line.py        # JournalLine
└── posting/
    ├── dtos.py            # PostingViewModel (output-only — no input DTO)
    ├── repo.py             # PostingRepo — abstract persistence contract
    ├── service.py          # PostingService — post/get-by-account/get-by-journal-number
    └── schemas/
        └── ledger_posting.py  # LedgerPosting (frozen)
```

Each feature module is self-contained: its own DTOs, its own repository contract, its
own service, its own schemas. `posting` depends on `journal`, which depends on
`account` — never the reverse (enforced by an import-linter contract at the workspace
root).

## Public API

Import from each feature's package root, not from internal submodules:

```python
from trutina.core.account import (
    AccountService,
    AccountRepo,
    CreateAccountInput,
    UpdateAccountInput,
    AccountViewModel,
    ChartOfAccountsViewModel,
)
from trutina.core.journal import (
    JournalService,
    JournalRepo,
    CreateJournalInput,
    JournalLineInput,
    JournalViewModel,
    JournalLineViewModel,
)
from trutina.core.posting import (
    PostingService,
    PostingRepo,
    PostingViewModel,
)
```

Domain schemas (`Account`, `JournalEntry`, `JournalLine`, `LedgerPosting`,
`ChartOfAccounts`) are importable from their explicit submodule paths
(`trutina.core.account.schemas.account`, etc.) when you need the domain type itself
— for example, inside a repository adapter. Callers outside `core` should generally
work with DTOs and ViewModels instead.

## Usage

### Creating an account

```python
from trutina.core.account import AccountService, CreateAccountInput
from trutina.core.account.schemas.account import AccountCategory

service = AccountService(repo)  # repo: any AccountRepo implementation

account = await service.create_account(
    CreateAccountInput(code="1001", name="Cash", category=AccountCategory.ASSET)
)
# account.normal_balance == "debit"
```

### Creating a balanced journal entry

```python
from datetime import datetime
from decimal import Decimal
from trutina.core.journal import JournalService, CreateJournalInput, JournalLineInput

journal_service = JournalService(journal_repo, account_service)

entry = await journal_service.create_journal_entry(
    CreateJournalInput(
        posting_date=datetime(2025, 1, 1),
        lines=[
            JournalLineInput(account="Cash", debit_amount=Decimal("100.00")),
            JournalLineInput(account="Sales Revenue", credit_amount=Decimal("100.00")),
        ],
        description="Cash sale",
    )
)
# entry.is_balanced == True
```

An unbalanced entry, an unknown account, or a future-dated entry raises before
anything is persisted — see [Error Handling](#error-handling).

### Posting a journal entry to the ledger

```python
from trutina.core.posting import PostingService

posting_service = PostingService(posting_repo, journal_service)

postings = await posting_service.post_journal_entry(entry.journal_number)
# one PostingViewModel per journal line; posting the same entry twice raises
```

## Integration With the Rest of the Repository

```text
apps/cli, apps/api
        │  (constructs concrete repos, injects into services)
        ▼
trutina-infrastructure   (Mongo* repos implementing AccountRepo/JournalRepo/PostingRepo)
        │
        ▼
trutina-core             ← you are here
        │
        ▼
trutina-shared           (validation helpers, error model)
```

Core never imports `trutina-infrastructure`, `trutina-cli`, or `trutina-api`. It is
handed a concrete repository at service-construction time by whichever app or
infrastructure layer wires the graph together — core has no opinion on what that
repository is backed by.

## Extending This Package

Adding a new operation to an existing feature (e.g. a new `AccountService` method):

1. Add any new DTO/ViewModel fields to `dtos.py` first — service methods should
   accept and return DTOs, never raw domain objects, at the public boundary.
2. Add the repository method to the abstract `*Repo` class if new persistence access
   is needed, with a docstring describing the contract any adapter must satisfy.
3. Implement the service method. Construct domain schemas (`Account`,
   `JournalEntry`, etc.) inside the service — validation happens at construction time
   via Pydantic, and `ValidationError` should be caught and re-raised as
   `ValidationAppError`.
4. Add unit tests against a `Fake*Repo` (see [Testing](#testing)).

Adding a new feature module (e.g. a future `reporting` module):

1. Mirror the existing shape: `dtos.py`, `repo.py`, `service.py`, `schemas/`, `tests/`.
2. Respect the internal layering — a new module may depend on `account`, `journal`,
   or `posting` per the same rules those three already follow, but the import-linter
   contract must be updated if you introduce a new directional dependency.
3. Keep the module free of `beanie`/`pymongo` imports — the workspace-level
   import-linter contract enforces this for all of `trutina.core`.

## Error Handling

Every error that can cross a service boundary is either `AppError` or its subclass
`ValidationAppError`, both from `trutina-shared`. Domain construction failures
(a Pydantic `ValidationError` raised by a schema) are caught by the service and
re-raised as `ValidationAppError`; business-rule failures (duplicate code, unknown
account, already-posted journal entry) are raised directly as `AppError` with a
specific `ErrorCode`.

Confirmed codes used by this package's services: `DUPLICATE_ACCOUNT_CODE`,
`DUPLICATE_ACCOUNT_NAME`, `UNKNOWN_ACCOUNT`, `UNKNOWN_JOURNAL_ENTRY`,
`JOURNAL_ALREADY_POSTED`, `VALIDATION_ERROR` (wrapping domain validators). Callers
should match on `AppError.code`, not on exception type alone, since every service
failure surfaces through the same two exception classes.

## Testing

Core's own tests live beside the code (`account/tests/`, `journal/tests/`,
`posting/tests/`), split `test_*_unit.py` (fake-repo, `@pytest.mark.unit`) and
`test_*_integration.py` (real MongoDB via `trutina-infrastructure`,
`@pytest.mark.integration`). Shared fixtures/factories/fakes live at the workspace
root under `tests/`.

Run just this package's fast suite:

```bash
uv run pytest -m "unit and core"
```

Run its integration suite (requires MongoDB — see root `compose.yml` or
`.env.test.example`):

```bash
uv run pytest -m "integration and core"
```

When writing new service tests, substitute the repository with the matching
`Fake*Repo` from `tests/fakes/` rather than mocking — domain schemas should be
constructed directly with no mocking at all. See
`Trutina Unit Testing Prompt — Condensed Reference.md` at the repo root for the full
project testing standard.

## What Consumers Should Know

- **Services are the only supported entry point.** Don't construct `Account`,
  `JournalEntry`, or `LedgerPosting` directly from outside this package — construct
  them through the corresponding service so validation and business rules run.
- **`CreateJournalInput` never carries a journal number.** `JournalService` assigns
  it via `JournalRepo.next_journal_number()`.
- **`PostingViewModel` has no matching input DTO.** Postings are always derived
  internally by `PostingService` from an already-persisted `JournalViewModel`; there
  is nothing for a caller to submit.
- **Posting an entry twice raises, it doesn't silently no-op.** Callers must catch
  `AppError` with `ErrorCode.JOURNAL_ALREADY_POSTED` if retry logic is possible on
  their side.
- **Account name matching is case-insensitive** via `account_lookup_key()` in
  `trutina-shared`; display casing is preserved as originally entered.
