"""
CLI-argument-to-value adapter for the Posting CLI feature.

Unlike account/parser.py and journal/parser.py, PostingService takes
plain scalars (int, str) rather than an input DTO — modules/posting/dtos.py
defines only PostingViewModel; there is no PostingService input DTO to
build, because postings are derived internally from an already-posted
JournalEntry rather than submitted by a caller. This module therefore
only validates and cleans the two raw values every posting command
needs: a journal number and an account identifier.

    Typer arguments -----> parse_*() -----> validated value
    Rich prompts (prompt.py) -----> parse_*() -----> validated value

Explicitly NOT this module's responsibility:

- Business or domain validation — UNKNOWN_JOURNAL_ENTRY / account
    resolution failures are raised by PostingService/JournalService
    once the value reaches the handler, not here.
- Calling services or repositories.
- Rich prompting, rendering, or console output.

This module must never be imported by service or domain code.
"""

import typer


def parse_journal_number(raw: str) -> int:
    """Resolve a raw journal-number string to an int.

    Mirrors journal/parser.py's parse_journal_number() exactly. Kept as
    a feature-local copy rather than an import from the journal feature
    — each CLI feature owns its own input-validation rules
    independently, even where the rule is momentarily identical, so
    that the two features never depend on each other's CLI internals.

    Args:
        raw: Raw journal-number string, as typed or prompted.

    Returns:
        The parsed journal number.

    Raises:
        typer.BadParameter: If ``raw`` is not a valid integer.
    """
    try:
        return int(raw.strip())
    except ValueError:
        raise typer.BadParameter(f"'{raw}' is not a valid journal number.") from None


def parse_account_identifier(raw: str) -> str:
    """Clean a raw account identifier string.

    Only strips incidental surrounding whitespace — this is not
    resolution or existence-checking, which PostingService performs
    downstream via account_lookup_key() case-insensitive matching.

    Args:
        raw: Raw account name, as typed or prompted.

    Returns:
        The cleaned account identifier.
    """
    return raw.strip()
