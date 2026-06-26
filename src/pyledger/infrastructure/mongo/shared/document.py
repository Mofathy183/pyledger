"""Shared MongoDB base document with automatic timestamp management.

TimestampedDocument provides the common persistence fields shared by all
MongoDB documents in the infrastructure layer. It automatically records
when a document is first persisted and when it was most recently written,
ensuring consistent audit metadata across every collection without
duplicating timestamp logic in individual document models.

Timestamp lifecycle
-------------------
- created_at is assigned exactly once immediately before the document's
    first insert into MongoDB.
- updated_at is initialized to the same value on insert and is expected
    to be refreshed by repository write operations on subsequent updates.
- Both timestamps are stored in UTC to provide a consistent time
    reference across environments.

Architectural responsibility
----------------------------
This class belongs entirely to the infrastructure layer. It provides
persistence metadata only and intentionally contains no business rules,
domain validation, or accounting logic.
"""

from datetime import UTC, datetime

from beanie import Document, Insert, before_event


class TimestampedDocument(Document):
    """Base Beanie document providing common audit timestamps.

    All MongoDB persistence models inherit from TimestampedDocument to
    obtain consistent creation and modification timestamps. The timestamps
    are infrastructure-managed metadata and are not part of the domain
    model or business invariants.

    Attributes:
        created_at: UTC timestamp recorded when the document is first
            inserted into MongoDB.
        updated_at: UTC timestamp representing the most recent write to
            the document.
    """

    created_at: datetime | None = None
    updated_at: datetime | None = None

    @before_event(Insert)
    def initialize_timestamps(self) -> None:
        """Initialize persistence timestamps before the first insert.

        Beanie invokes this hook immediately before inserting a new
        document. Both timestamps receive the same UTC value so newly
        created documents begin with identical creation and modification
        times. Repository update operations are responsible for advancing
        ``updated_at`` on subsequent writes.
        """
        now = datetime.now(UTC)
        self.created_at = now
        self.updated_at = now
