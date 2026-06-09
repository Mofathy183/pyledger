from collections.abc import Generator
from datetime import datetime


def default_posting_date() -> datetime:
    """
    it will make default date for the journal entry will add which will be the current day

    :return: the date of today without the time
    """
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    return today


def journal_generator_number(
    latest_journal_num: int | None = None,
) -> Generator[int]:
    """
    that a function that made to help generate number for the journal entry
    to record each entry with a number like id

    and it will take the latest number that save the entries and start generate after that one
    or start from 1

    :param latest_journal_num: Optional use when need to generate the next number of the latest one you have
    :return: the generated value to use it in next() to get the number

    Example::

        >>> next(journal_generator_number())
        1
        >>> next(journal_generator_number(8))
        9
    """
    num = latest_journal_num if latest_journal_num else 0
    while True:
        num += 1
        yield num
