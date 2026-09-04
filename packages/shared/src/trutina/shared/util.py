from datetime import datetime


def default_posting_date() -> datetime:
    """Return the current local date with its time component set to midnight."""
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    return today
