from datetime import date, timedelta
from typing import Optional, Tuple


def iteration_dates(dt: Optional[date] = None) -> Tuple[date, date]:
    """
    Iteration start and stop dates.
    By default returns next iteration ones.

    >>> iteration_dates(date(2020, 1, 20))
    (datetime.date(2020, 1, 21), datetime.date(2020, 1, 27))
    >>> iteration_dates(date(2020, 1, 21))
    (datetime.date(2020, 1, 28), datetime.date(2020, 2, 3))
    >>> iteration_dates(date(2020, 1, 24))
    (datetime.date(2020, 1, 28), datetime.date(2020, 2, 3))
    """
    dt = dt or date.today()
    _, offset = divmod(6 - dt.weekday() + 2, 7)
    start = dt + timedelta(days=offset or 7)
    return start, start + timedelta(days=6)


def iteration_start(dt: Optional[date] = None) -> date:
    start, _ = iteration_dates(dt)
    return start


def iteration_stop(dt: Optional[date] = None) -> date:
    _, stop = iteration_dates(dt)
    return stop
