"""Shared API-layer test factories.

Phase 1 of the API testing foundation (see `PyLedger API Testing
Architecture`, Section 5). Only genuinely feature-agnostic, currently
useful helpers are implemented here:

    make_headers
    build_url

`make_auth_headers`, `make_pagination_params`, `make_error_response_payload`,
and `make_query_filter` are deliberately deferred — each depends on a
capability (auth, pagination, a defined error envelope) that does not
exist in the codebase yet. Adding them now would mean guessing a shape
that is likely to be rewritten once the real feature lands.
"""

from urllib.parse import urlencode


def make_headers(**overrides: str) -> dict[str, str]:
    """Build a base request header dict with override support.

    Starts from a minimal JSON-request default and layers any
    caller-supplied overrides on top. Centralizing this avoids each
    route test hand-building the same header dict.

    Args:
        **overrides: Header name/value pairs to set or override on top
            of the default `content-type: application/json` header.

    Returns:
        The merged header dict.
    """
    headers = {"content-type": "application/json"}
    headers.update(overrides)
    return headers


def build_url(path: str, **query_params: object) -> str:
    """Build a request path with an optional query string.

    Centralizes query-string construction so tests don't hand-build
    `f"...?x={x}&y={y}"` strings. Parameters with a `None` value are
    omitted entirely, so callers can pass optional filters without
    conditional logic at the call site.

    Args:
        path: The base path, e.g. "/accounts".
        **query_params: Query parameters to encode. Any parameter whose
            value is `None` is skipped.

    Returns:
        `path` unchanged if no query parameters are given (or all are
        `None`); otherwise `path` followed by an encoded `?`-prefixed
        query string.
    """
    params = {k: v for k, v in query_params.items() if v is not None}

    if not params:
        return path

    return f"{path}?{urlencode(params)}"
