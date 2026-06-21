from datetime import datetime


def default_posting_date() -> datetime:
    """
    it will make default date for the journal entry will add which will be the current day

    :return: the date of today without the time
    """
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    return today
