# Trutina Roadmap

## Purpose

This roadmap lists the remaining work needed to turn the code into a complete bookkeeping application. The order is
intentional: finish the domain and service boundaries before adding storage, reporting, or integration layers.

## Roadmap Principles

- Keep accounting correctness ahead of persistence.
- Keep the domain independent of the CLI and Rich formatting.
- Add infrastructure only after the accounting model is stable.
- Prefer small, testable increments.
- Do not mark a work item complete unless the code exists in the repository and is coherent with the surrounding modules.

## Remaining Work

- Add storage-level uniqueness enforcement where needed.
- Add trial balance, reporting, and historical views.
- Add import/export and external integration surfaces.

## Workstreams

### CLI Presentation

- CLI presentation is complete for account, journal, and posting workflows: Typer command groups, parsers, prompts,
  handlers, formatters, shared Rich UI, and the shared error boundary are all implemented and tested.
- Add CLI tests for any new feature as it's introduced (pattern established — see `src/trutina/cli/README.md`
  §16, "Adding a New Feature").
- Future CLI work is limited to new command groups (e.g. reporting commands, once a reporting pipeline exists) and
  any shell-completion or interactive-workflow enhancements — see `src/trutina/cli/README.md` §18, "Future Work".

### Storage

- Add storage-level uniqueness enforcement where needed.

### Reporting

- Add trial balance calculation.
- Add account balance summaries.
- Add historical report views.
- Add future financial statement support.

### Integrations

- Add CSV or structured import/export.
- Add machine-readable output formats.
- Add external integration surfaces.

## Success Criteria

Trutina should be considered on track when:

- journal entries are always validated before acceptance,
- journal numbering remains deterministic,
- posting derivation remains deterministic,
- repository contracts are stable,
- storage is isolated behind interfaces,
- CLI error rendering matches the shared error model (confirmed implemented and tested via `error_boundary()`),
- trial balance reporting is available,
- the CLI stays thin,
- future features do not weaken the accounting model.
