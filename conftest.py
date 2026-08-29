"""
Root pytest configuration: fixture plugin registration and marker enforcement.

This file is collected once per test session (pytest.ini's `pythonpath = .`
makes it discoverable from the repo root) and is responsible for two
cross-cutting concerns that no individual package should have to repeat:

1. Registering the shared fixture plugins used across packages/apps.
2. Enforcing Trutina's two-axis marker discipline (see
    `pytest_collection_modifyitems` below) so `pytest -m "unit and cli"`,
    `pytest -m "integration and infra"`, etc. remain trustworthy filters
    instead of decorative, hand-maintained metadata that silently drifts
    from the code's real location — the same kind of staleness this repo
    has already documented elsewhere (e.g. `cli/constants/errors.py` vs.
    `shared/errors`).
"""

import pathlib

import pytest

pytest_plugins = [
    "tests.fixtures.account",
    "tests.fixtures.posting",
    "tests.fixtures.journal",
    "tests.fixtures.mongo",
    "tests.fixtures.settings",
    "tests.fixtures.services",
    "tests.fixtures.cli",
    "tests.fixtures.api",
]

# ── Marker taxonomy ──────────────────────────────────────────────────────
#
# Every collected test must carry exactly one marker from each axis:
#
#   Speed axis   {"unit", "integration"} — hand-written on the test itself.
#                Whether a test performs real I/O is a fact about its own
#                body, not its file location, so it can never be derived
#                and must always be written explicitly.
#
#   Layer axis   {"core", "infra", "cli", "api", "shared"} — derived from
#                the test file's path and applied automatically. Hand-
#                writing a layer marker is a collection error: the marker
#                must always agree with where the file actually lives, so
#                letting it be derived is what keeps it from rotting.
#
# The two axes are fully orthogonal. Every layer can legitimately pair
# with either speed marker (e.g. `infra` covers both slow, Mongo-backed
# repository tests and fast, pure error-translation tests that happen to
# live under `infrastructure/`) — there is no forbidden combination.

_SPEED_MARKERS: frozenset[str] = frozenset({"unit", "integration"})
_LAYER_MARKERS: frozenset[str] = frozenset({"core", "infra", "cli", "api", "shared"})

# Directory name -> layer marker, checked in this order. Order only matters
# for the (currently hypothetical) case where a path could contain more
# than one of these directory names — e.g. a future apps/api/core/ package.
# The first match wins, so more specific/authoritative directory names
# should be listed first if that situation ever arises.
_LAYER_DIRS: dict[str, str] = {
    "core": "core",
    "infrastructure": "infra",
    "cli": "cli",
    "api": "api",
}

# Directory names that both map to the single "shared" layer marker.
# Kept as a separate set (rather than folded into _LAYER_DIRS) because
# "shared" is the one layer with more than one owning directory
# (root shared/ and config/), and because the marker name intentionally
# does not match either directory name 1:1.
_SHARED_DIRS: frozenset[str] = frozenset({"shared", "config"})


def _derive_layer(path_parts: tuple[str, ...]) -> str | None:
    """Infer a test's layer marker from its file path.

    Walks `_LAYER_DIRS` in order and returns the marker for the first
    directory name found in `path_parts`; falls back to "shared" if the
    path instead passes through one of `_SHARED_DIRS`. Returns None when
    the path matches neither, which the caller treats as a hard
    collection error rather than an unmarked test — an unrecognized
    location almost always means `_LAYER_DIRS`/`_SHARED_DIRS` need a new
    entry for a new package, not that the test should go unclassified.

    Args:
        path_parts: The test file's path, pre-split via `Path.parts` so
            matching is exact-segment (e.g. "core") rather than a raw
            substring search that could false-positive on something like
            "cliff/".

    Returns:
        The derived layer marker name, or None if no known directory
        segment was found.
    """
    for dirname, marker in _LAYER_DIRS.items():
        if dirname in path_parts:
            return marker

    if any(shared_dir in path_parts for shared_dir in _SHARED_DIRS):
        return "shared"

    return None


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Enforce and auto-apply Trutina's two-axis test marker discipline.

    Every collected test must resolve to exactly one speed marker
    (hand-written) and exactly one layer marker (derived from its file
    path and applied here). This hook is the single source of truth for
    that rule, so a mis-tagged or unclassified test fails collection
    loudly, in one batched report, rather than silently producing a
    marker filter (`pytest -m "unit and infra"`) that quietly excludes
    or includes the wrong tests.

    Deliberately fails the whole collection (via `pytest.UsageError`)
    rather than warning, mirroring `--strict-markers` already configured
    in pytest.ini: marker hygiene here is a correctness gate, not a
    lint suggestion, because every other convention in this document
    (targeted `-m` runs in CI, `tools/pre-push.sh`) depends on markers
    being accurate.

    Args:
        config: The pytest session config (required by the hook
            signature; unused here).
        items: All collected test items, mutated in place by adding the
            derived layer marker to each.

    Raises:
        pytest.UsageError: If any item is missing a speed marker, carries
            more than one speed marker, has a hand-written layer marker
            that disagrees with its derived path-based marker, or lives
            at a path that doesn't resolve to any known layer.
    """
    violations: list[str] = []

    for item in items:
        path_parts = pathlib.Path(str(item.fspath)).parts
        own_markers = {marker.name for marker in item.iter_markers()}

        # --- Speed axis: must be hand-written, exactly one. ---
        declared_speed = _SPEED_MARKERS.intersection(own_markers)
        if len(declared_speed) != 1:
            violations.append(
                f"{item.nodeid}: must carry exactly one of "
                f"{sorted(_SPEED_MARKERS)}, found {sorted(declared_speed)}"
            )

        # --- Layer axis: derived from path, exactly one, never hand-written. ---
        derived_layer = _derive_layer(path_parts)
        declared_layer = _LAYER_MARKERS.intersection(own_markers)

        if derived_layer is None:
            violations.append(
                f"{item.nodeid}: path does not map to any known layer "
                f"{sorted(_LAYER_MARKERS)}; move the file under a "
                f"recognized package directory or update _LAYER_DIRS/"
                f"_SHARED_DIRS in conftest.py"
            )
        elif declared_layer and declared_layer != {derived_layer}:
            violations.append(
                f"{item.nodeid}: path implies layer marker "
                f"'{derived_layer}' but test declares "
                f"{sorted(declared_layer)} — remove the hand-written "
                f"layer marker; layer markers are derived from file "
                f"path, never authored on the test"
            )
        else:
            item.add_marker(getattr(pytest.mark, derived_layer))

    if violations:
        report = "\n".join(f"  - {violation}" for violation in violations)
        raise pytest.UsageError(f"Marker validation failed:\n{report}")
