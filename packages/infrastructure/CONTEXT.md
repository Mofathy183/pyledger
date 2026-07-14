# pyledger-infrastructure — Architectural Context

This document explains why `pyledger-infrastructure` is shaped the way it is.
For how to use it, see `README.md`. Nothing here should be duplicated there.

## Why this architecture

**Dependency inversion, not just separation.** `pyledger-core` defines
`AccountRepo`, `JournalRepo`, and `PostingRepo` as abstract contracts with
zero MongoDB or Beanie awareness. This package depends _on_ core to implement
those contracts — core never depends on this package. The payoff is that the
accounting domain can be tested, read, and reasoned about without a database
running, and a second storage backend (see "Extension points" below) can be
added later by satisfying the same three ABCs, with no change to any service
or domain schema.

**One executor, one error-translation seam.** Every repository method routes
its Beanie call through `MongoExecutor.run(coro)`, which wraps the call in
`translate_mongo_errors()`. This exists so that storage-specific concerns —
today, exception translation; in the future, logging, metrics, retries, or
transaction coordination — have exactly one place to be added, rather than
requiring every repository method to be revisited individually. This is
stated as the explicit design intent in `MongoExecutor`'s own docstring, not
an incidental convenience.

**One mapping boundary per adapter.** Each repository defines exactly one
`_to_document()` and one `_to_domain()` static method. Every field written to
or read from MongoDB passes through that single boundary. This is what makes
it safe to reason about serialization correctness (e.g. Decimal encoding) by
reading one method instead of auditing every call site that touches Mongo.

**Domain validation re-runs on reconstruction.** `_to_domain()` always
constructs a real domain object (`Account(...)`, `JournalEntry(...)`,
`LedgerPosting(...)`), not a bypassed/`model_construct`-style shortcut. This
means every invariant the domain model enforces (balance, single-sidedness,
date ranges) is re-checked on every read, not just on write — storage
corruption or a bad migration surfaces as a validation error at read time
rather than silently propagating into the accounting workflow.

## Trade-offs accepted

- **No multi-document transactions.** `MongoPostingRepo.save_many()` uses a
  single `insert_many()` call with no `ClientSession`. This was accepted
  because no transaction infrastructure exists anywhere in the workspace yet,
  and adding one for a single call site would be premature. The cost is a
  documented, accepted gap: a mid-batch interruption can partially persist a
  journal's postings, and a concurrent posting attempt can race past
  `PostingService`'s existence pre-check before either write lands. This is
  the same category of TOCTOU window already accepted in
  `AccountService.create_account()`.
- **Two round-trips on account update.** `MongoAccountRepo.update()` loads
  the existing document (to preserve `_id` and `created_at`) before calling
  `replace()`. A single upsert-style call would be cheaper, but `Document.save()`
  performs an upsert, which risks silently recreating a deleted account.
  `replace()` without upsert, plus the extra read, was chosen to keep
  "update a missing account raises `UNKNOWN_ACCOUNT`" a guaranteed contract
  rather than an accidental one.
- **Amounts stored as decimal strings, not BSON `Decimal128`.** Beanie's
  default codec has no lossless native decimal type readily available for
  this use case, so every monetary field is encoded as a string and decoded
  with `Decimal(value)` on read. This trades index-friendliness and
  range-query ergonomics (a future trial-balance query over amounts would
  need to decode first) for a simpler, precision-guaranteed encoding today.
  Changing this later requires a data migration, not just a code change.
- **`journal_number` allocation bypasses Beanie.** `next_journal_number()`
  talks to a raw, non-Beanie-registered `counters` collection via the Motor
  API directly, using `translate_mongo_errors()` standalone rather than
  through `MongoExecutor`. This was necessary because Beanie has no built-in
  primitive for atomic counter increments — it is the one place in this
  package that deliberately steps outside the executor pattern, and that
  exception is documented at the call site.

## Invariants that must never be broken

- **Core has zero Mongo/Beanie awareness.** Enforced mechanically: the root
  `pyproject.toml`'s import-linter configuration includes a `forbidden`
  contract making `beanie`/`pymongo` imports inside `pyledger.core` a build
  failure. This package exists specifically so core never needs either.
- **Layered dependency direction.** The root import-linter `layers` contract
  fixes the order `pyledger.cli | pyledger.api` → `pyledger.infrastructure` →
  `pyledger.core` → `pyledger.shared | pyledger.config`. This package must
  never import from `pyledger.cli` or `pyledger.api`.
- **No business rules in a repository.** Uniqueness pre-checks, the
  one-posting-per-journal invariant, chart-of-accounts resolution — none of
  it belongs here. A repository's only job is mapping and persistence.
- **`_to_document()`/`_to_domain()` are the only mapping path.** No other
  code should hand-construct a `*Document` for persistence, or hand-build a
  domain object from a raw Mongo result.
- **`DuplicateKeyError` must be caught before entering
  `translate_mongo_errors()` on any write path.** `DuplicateKeyError` is a
  `PyMongoError` subclass; if a write method enters the generic translation
  context without an outer `except DuplicateKeyError` clause first, a real
  uniqueness violation silently collapses into `AppError.unknown()` instead
  of the specific conflict error a caller needs. This is explicitly called
  out and unit-tested in `error_translation.py`.
- **Derived/computed domain fields are never persisted.** `normal_balance`,
  `total_debits`/`total_credits`/`is_balanced`, and `is_debit` are recomputed
  on reconstruction, never stored — storing them would create a second
  source of truth that could silently diverge from the fields they're
  derived from.
- **Callers must initialize Beanie first.** Every repository assumes
  `init_beanie()` has already registered its `Document` class. This package
  does not call `init_beanie()` itself — that is a composition-root
  responsibility (`CliContext`, the API's bootstrap), kept out of this
  package so it stays agnostic to _when_ and _how often_ a caller wants to
  initialize.

## Allowed and forbidden dependencies

**Allowed** (per `packages/infrastructure/pyproject.toml`): `pyledger-shared`,
`pyledger-core`, `pyledger-config`, `beanie`, `pymongo`.

**Forbidden:** `pyledger-cli`, `pyledger-api`, or any other `apps/*` package;
any presentation library (`typer`, `rich`, `fastapi`, `strawberry-graphql`).
None of these appear as dependencies today, and none should be added — a
storage adapter has no legitimate reason to know about a transport or UI
layer.

## Layering within this package

There is no import-linter contract scoped _inside_ `pyledger.infrastructure`
today — the root workspace only enforces the account→journal→posting order
within `pyledger.core` itself. In practice, `mongo/journal/` and
`mongo/posting/` each import only their own domain package from core (e.g.
`mongo/posting/repository.py` imports `pyledger.core.posting`, not
`pyledger.core.journal`), mirroring core's dependency order, but this is
convention observed in the current source rather than something CI currently
fails a build over. Flagging this rather than describing it as enforced.

## Control and data flow

```txt
Service (pyledger-core)
    -> Repo contract call (AccountRepo / JournalRepo / PostingRepo)
        -> Mongo*Repo method
            -> MongoExecutor.run(coroutine)
                -> translate_mongo_errors() context
                    -> Beanie / raw PyMongo call
            <- result
        <- _to_domain() reconstructs and re-validates the domain object
    <- ViewModel / domain object returned to the service
```

Write paths that can raise `DuplicateKeyError` (`create()`, `save()`) catch it
_outside_ `MongoExecutor.run()` and delegate to a per-repository
`_on_duplicate()` method, which inspects the violated index name
(`violated_index()`) to decide which domain conflict to raise.

## Extension points

- **A second storage backend.** Any package implementing `AccountRepo`,
  `JournalRepo`, and `PostingRepo` against a different datastore (e.g. a
  future `pyledger-storage-postgres`) is a legitimate sibling to this
  package — it would prove the contracts are genuinely storage-agnostic
  rather than MongoDB-shaped in disguise. No such package exists yet.
- **A new bounded-context adapter.** Mirrors the `account`/`journal`/
  `posting` shape exactly — see the README's "Extending" section for the
  concrete steps.
- **Cross-cutting execution concerns.** `MongoExecutor` is the intended seam
  for adding logging, metrics, retries, or (eventually) transaction/session
  support to every repository at once, without touching individual
  repository methods. This is stated as forward-looking intent in
  `MongoExecutor`'s own docstring — no such behavior is implemented today.

## Assumptions this package relies on

- A caller has already run `init_beanie()` with the relevant `Document`
  classes registered before constructing any `Mongo*Repo`.
- Exactly one MongoDB connection/event-loop pairing is active per process at
  a time from this package's point of view; coordinating that (e.g. the
  CLI's single `BlockingPortal` vs. the API's ASGI-owned loop) is the
  caller's responsibility, not something this package arbitrates.
- `MongoSettings` is fully resolved before `connect()` is called — this
  package never reads environment variables or calls `get_settings()`
  itself.

## Common mistakes to avoid

- Entering `translate_mongo_errors()` on a write path without first catching
  `DuplicateKeyError` — the violation silently becomes `AppError.unknown()`
  instead of a specific conflict.
- Adding an existence check, uniqueness check, or any other business rule
  inside a repository method instead of the calling service.
- Persisting a computed/derived domain field (`normal_balance`,
  `is_balanced`, `is_debit`, `total_debits`/`total_credits`).
- Calling Beanie or PyMongo directly from a repository method instead of
  routing through `MongoExecutor.run()` — this silently loses error
  translation.
- Forgetting to add a new `Document` subclass to the production
  `init_beanie()` call site and to
  `tests/fixtures/mongo.py::DOCUMENT_MODELS` when adding a new bounded
  context — the symptom is a `CollectionWasNotInitialized` error that only
  appears the first time the new repository is actually used.
