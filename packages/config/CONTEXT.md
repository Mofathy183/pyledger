# pyledger-config — Context

This document explains why `pyledger-config` is shaped the way it is.
For usage, see `README.md`. This file rarely discusses usage and the
README rarely discusses architecture — if something appears in both,
it's for a different reason each time.

## Why this architecture was chosen

PyLedger has multiple applications (`pyledger-cli`, `pyledger-api`, and
future apps per the monorepo plan) and a storage adapter
(`pyledger-infrastructure`) that all need the same categories of
configuration — a Mongo connection, API bind settings — sourced the
same way. The alternative (`os.environ` reads scattered across each
app) would mean re-deriving env-var naming, dotenv loading, and
test/production isolation independently in every consumer, with no
guarantee they'd agree on a prefix convention or a nesting delimiter.

`pydantic-settings`'s `BaseSettings` was chosen (over hand-rolled
`os.environ.get(...)` parsing, or a plain `BaseModel` populated by a
caller) specifically because it gives typed validation, a documented
`env_nested_delimiter`, and dotenv-file loading for free, and because
`pydantic` is already the project's validation library everywhere else
— introducing a second config-parsing dependency would be inconsistent
with that.

## Alternatives considered

- **One flat `Settings` model with no nesting** (`mongo_uri`,
  `mongo_db`, `api_host`, `api_port` as top-level fields). Rejected:
  as the number of settings groups grows (a future `WorkerSettings`,
  `AuthSettings`), a flat model becomes an undifferentiated field list
  with no way to tell which fields belong to which subsystem at a
  glance. Nesting (`settings.mongo.uri`, `settings.api.port`) keeps
  each group's fields visibly grouped and independently reusable —
  `pyledger-infrastructure` only ever needs `MongoSettings`, not the
  whole `Settings` object.
- **Passing raw environment variables into each consumer.** Rejected:
  this is precisely the "N independently drifting copies of the same
  rule" failure mode the project's own architecture documents warn
  against for business logic, and configuration parsing is no
  different — a typo in an env var name should fail once, at one
  well-tested boundary, not silently produce `None` in three different
  places.
- **A single settings class with a runtime "test mode" flag** instead
  of a separate `TestSettings` subclass. Rejected: a boolean flag
  threaded through every field access is easy to forget to check and
  easy to leave set by accident between tests. A distinct class with
  its own `env_prefix`/`env_file` makes the two configurations
  structurally incapable of reading each other's variables — the
  isolation is enforced by type, not by convention.

## Trade-offs accepted

- **`get_settings()`'s `lru_cache` makes configuration effectively
  process-global.** This is deliberate — repeatedly re-parsing the
  environment on every access would be wasteful and would risk a
  settings object changing mid-request if the environment mutated
  concurrently. The accepted cost is that tests which mutate
  environment variables must explicitly clear the cache, which is why
  the isolation fixture exists as shared test infrastructure rather
  than being left to each test file to remember.
- **Nested settings models (`MongoSettings`, `ApiSettings`) are plain
  `BaseModel`, not `BaseSettings`.** Only the root `Settings`/
  `TestSettings` classes own env-prefix and dotenv-file configuration.
  This means a nested settings object can never be constructed
  standalone from the environment — it must always be built as part of
  the root model's `default_factory`. That's an accepted constraint,
  not an oversight: giving every nested model its own independent
  `BaseSettings` config would create ambiguity about which prefix wins
  when a nested model is used outside of `Settings`.

## Design decisions future contributors should preserve

- Every settings group (`MongoSettings`, `ApiSettings`, and any future
  addition) stays a plain `BaseModel` nested inside `Settings` — never
  its own independently-loaded `BaseSettings`.
- `TestSettings` stays a subclass of `Settings`, not a structurally
  independent model, so any field added to `Settings` is automatically
  available (under the test prefix) without a second definition.
- `get_settings()` stays the single cached accessor for production
  code. Constructing `Settings()` directly is reserved for tests and
  explicit override scenarios — application composition roots should
  call `get_settings()`, not `Settings()`, so there's exactly one
  cached instance per process.

## Architectural invariants that must never be broken

- **Zero dependencies on any other `pyledger-*` package.** This package
  sits at the root of the workspace dependency graph (confirmed by its
  `pyproject.toml`: only `pydantic` and `pydantic-settings`). If this
  package ever needs to import from `pyledger.core` or
  `pyledger.infrastructure`, that is a sign the code doesn't belong
  here.
- **No I/O beyond dotenv-file reads performed by `pydantic-settings`
  itself.** This package must never open a network connection, read a
  database, or otherwise perform work beyond parsing configuration.
- **Production and test configuration must remain namespace-isolated.**
  `PYLEDGER_` vs. `PYLEDGER_TEST_`, `.env` vs. `.env.test`. A change
  that lets test configuration silently fall back to reading production
  variables (or vice versa) is a correctness regression, not a
  refactor.

## Allowed dependencies

- `pydantic` — field validation and model definitions.
- `pydantic-settings` — environment/dotenv loading, `env_nested_delimiter`.
- Python standard library (`functools.lru_cache`).

## Forbidden dependencies

- Any other `pyledger-*` workspace package (`pyledger-core`,
  `pyledger-infrastructure`, `pyledger-cli`, `pyledger-api`). This
  package is a dependency root; nothing here may depend on anything
  downstream of it.
- Any driver or client library for a specific backend (`pymongo`,
  `beanie`, an HTTP client, etc.) — this package describes
  configuration shape, it does not use the configuration to connect to
  anything.

## Layering rules

`pyledger-config` has no internal layers of its own beyond three
sibling files (`mongo.py`, `api.py`, `base.py`) plus `__init__.py`.
The only ordering rule: `base.py` may import from `mongo.py`/`api.py`
(to nest them into `Settings`), never the reverse — a nested settings
module must never import the root `Settings`/`TestSettings` classes.

## Control flow

1. An application composition root calls `get_settings()` (or
   constructs `Settings()`/`TestSettings()` directly, in tests).
2. `pydantic-settings` reads the relevant dotenv file (if present) and
   overlays matching `PYLEDGER_`/`PYLEDGER_TEST_`-prefixed environment
   variables.
3. Nested fields (`mongo`, `api`) are populated from
   double-underscore-delimited variables (`PYLEDGER_MONGO__URI`) or
   fall back to each nested model's own `Field(default=...)` values if
   unset.
4. The resulting `Settings`/`TestSettings` instance is handed to
   whatever needs it (`connect(settings.mongo)`, `uvicorn.run(host=
settings.api.host, ...)`), by the caller — this package never passes
   its own output anywhere itself.

## Data flow

Environment variables and dotenv files are the only data sources. There
is no reverse flow — nothing in this package writes to the environment,
persists settings, or mutates its own output after construction.

## Extension points

- New settings groups: add a `BaseModel` file, nest it into `Settings`
  with a `default_factory`, re-export it — see README's "Extending this
  package" for the mechanical steps.
- New fields on an existing group: add a `Field(...)` with a sensible
  default and a description; no other file needs to change unless the
  field affects `TestSettings`' isolation story (it won't, since
  `TestSettings` inherits the same field set).

## Assumptions this package relies on

- Callers that need test isolation between environment-variable
  mutations will clear `get_settings`'s cache (directly, or via the
  shared `isolate_settings_cache` fixture) — this package does not
  enforce that itself.
- `.env`/`.env.test` files, if present, are trusted local input — this
  package performs no secrets-manager integration and assumes
  production secrets are supplied via real environment variables, not
  a committed dotenv file (see the repo-wide monorepo architecture
  document's Secrets Management section for the broader policy this
  package is expected to plug into once a secrets backend exists).

## Common mistakes to avoid

- **Calling `Settings()` directly in application code instead of
  `get_settings()`.** This bypasses the cache and can produce a second,
  independently-constructed settings object mid-process — use
  `get_settings()` in production code paths; reserve direct
  construction for tests and explicit overrides.
- **Forgetting to clear the `get_settings` cache after mutating
  environment variables in a test.** If you're writing a test outside
  the shared fixture infrastructure, remember `get_settings` is
  process-cached — a `monkeypatch.setenv(...)` won't be reflected until
  the cache is cleared.
- **Giving a new nested settings model its own `BaseSettings`/env
  prefix.** Only `Settings`/`TestSettings` should ever own
  environment-loading configuration — a nested model added as
  `BaseSettings` will silently ignore the parent's prefix rules.
- **Assuming this package validates connectivity.** `MongoSettings`
  describes a URI/DB name; it does not verify a MongoDB instance is
  reachable at that URI — that check belongs to `pyledger-infrastructure`'s
  `connect()`.
