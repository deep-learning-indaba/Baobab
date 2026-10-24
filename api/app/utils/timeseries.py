from collections import Counter


def daily_counts(query, timestamp_column):
    """[(date, count)] of `query`'s rows by the date of `timestamp_column`, in
    date order, skipping rows without one.

    Grouped in Python rather than with CAST(... AS DATE): SQLite (the test
    database) returns only the year from that cast, while Postgres returns
    the date.
    """
    counts = Counter(
        timestamp.date()
        for (timestamp,) in query.with_entities(timestamp_column)
        if timestamp is not None
    )
    return sorted(counts.items())
