# pyledger-config

Typed, environment-driven configuration for PyLedger.

## What is this package?

`pyledger-config` (import path `pyledger.config`) provides the strongly
typed settings models every PyLedger application and storage adapter
reads its configuration from. It defines how configuration is sourced
(environment variables and optional dotenv files) and gives the rest of
the workspace one place to ask "what's the Mongo URI?" or "what port
should the API bind to?" instead of reading `os.environ` directly.

## Why does it exist?

Every app (`pyledger-cli`, `pyledger-api`) and the storage adapter
(`pyledger-infrastructure`) needs the same kind of information — where
MongoDB lives, what host/port the API binds to — but none of them
should each invent their own env-var parsing, their own test/production
isolation, or their own caching. This package is that one shared
answer.

## Responsibilities

- Define the typed settings surface (`Settings`, `TestSettings`,
  `MongoSettings`, `ApiSettings`).
- Load configuration from environment variables and an optional dotenv
  file.
- Keep test configuration namespaced and isolated from production
  configuration.
- Provide a single cached accessor (`get_settings()`) so the rest of
  the application doesn't re-parse the environment on every call.

## Public API

Everything below is re-exported from `pyledger.config`:

| Name             | What it is                                                            |
| ---------------- | --------------------------------------------------------------------- |
| `Settings`       | Root production configuration model.                                  |
| `TestSettings`   | `Settings` subclass loaded from a separate env namespace/dotenv file. |
| `MongoSettings`  | Nested MongoDB connection settings.                                   |
| `ApiSettings`    | Nested API-layer settings (host, port, reload, OpenAPI metadata).     |
| `get_settings()` | Cached (`lru_cache`) accessor returning a `Settings` instance.        |

This package has no other public surface — nothing under `pyledger.config`
outside of `__init__.py`'s re-exports should be imported directly.

## Installation / usage

Within the workspace, add it as a dependency in your package's
`pyproject.toml`:

```toml
dependencies = ["pyledger-config"]

[tool.uv.sources]
pyledger-config = { workspace = true }
```

Then:

```python
from pyledger.config import get_settings

settings = get_settings()
print(settings.mongo.uri)
print(settings.api.port)
```

For an isolated instance instead of the cached singleton (e.g. when
you need to pass explicit values), construct the model directly:

```python
from pyledger.config import Settings, MongoSettings

settings = Settings(mongo=MongoSettings(uri="mongodb://localhost:27017"))
```

### Environment variables

Production configuration reads from `PYLEDGER_`-prefixed variables and
an optional `.env` file at the repo root. Nested settings use a double
underscore (`__`) as the delimiter:

```bash
PYLEDGER_MONGO__URI=mongodb://localhost:27017
PYLEDGER_MONGO__DB=pyledger
PYLEDGER_API__HOST=127.0.0.1
PYLEDGER_API__PORT=8000
```

Test configuration reads the same shape under a `PYLEDGER_TEST_` prefix
from `.env.test`:

```bash
PYLEDGER_TEST_MONGO__URI=mongodb://localhost:27017
PYLEDGER_TEST_MONGO__DB=pyledger_test
```

See `.env.example` and `.env.test.example` at the repo root for the
full set of currently supported keys.

## Integration with the rest of the repository

- `pyledger-infrastructure` accepts a `MongoSettings` instance (never
  calls `get_settings()` itself — see that package's own docs).
- `pyledger-cli` and `pyledger-api` each call `get_settings()` at their
  own composition root and pass the nested settings down to whatever
  needs them.
- Nothing in `pyledger-config` imports from any other `pyledger-*`
  package — it sits at the root of the dependency graph.

## Extending this package

Adding a new settings group (e.g. a future `WorkerSettings`) means:

1. Add a new `BaseModel` (not `BaseSettings`) in its own file, following
   `mongo.py`/`api.py`'s shape — plain `Field(...)` defaults with
   descriptions, no env-loading logic of its own.
2. Add it as a field on `Settings` in `base.py` with a
   `default_factory`.
3. Re-export it from `__init__.py`.

Do not give a nested settings model its own `BaseSettings` /
`SettingsConfigDict` — only `Settings`/`TestSettings` own the
env-prefix and dotenv-file configuration. A nested model that tried to
load its own environment independently would silently stop respecting
`PYLEDGER_`/`PYLEDGER_TEST_` prefixing and nested-delimiter parsing.

## Testing

- Use `TestSettings()` directly for a settings instance that reads the
  `PYLEDGER_TEST_` namespace and `.env.test`.
- If a test mutates environment variables that affect settings, clear
  `get_settings`'s cache before and after — the shared
  `isolate_settings_cache` autouse fixture (`tests/fixtures/settings.py`)
  already does this for every test in the suite, so you don't normally
  need to call `get_settings.cache_clear()` yourself.
- The shared `test_settings` fixture (session-scoped) returns a
  `TestSettings()` instance for tests that need Mongo/API settings
  without constructing their own.

## Common usage examples

```python
# Composition root of an app, reading real settings
from pyledger.config import get_settings

settings = get_settings()
connection = await connect(settings.mongo)
```

```python
# A test overriding a single nested value
from pyledger.config import TestSettings, MongoSettings

settings = TestSettings(mongo=MongoSettings(db="pyledger_scratch"))
```

## What consumers should know

- `get_settings()` is cached for the life of the process. If you mutate
  environment variables after the first call, you must clear the cache
  (`get_settings.cache_clear()`) or you'll keep seeing stale values.
- `TestSettings` is a `Settings` subclass with a different env
  prefix/dotenv file — it is not a mock or a stub, it still reads real
  environment variables (just a different namespace).
- This package performs no I/O and has no side effects at import time
  beyond what `pydantic-settings` does to read `.env`/`.env.test`.
