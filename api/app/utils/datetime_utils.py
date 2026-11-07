import pytz


def event_local_date(utc_dt, tz_name):
    tz = pytz.timezone(tz_name or 'UTC')
    return utc_dt.replace(tzinfo=pytz.utc).astimezone(tz).date()


def event_local_datetime(utc_dt, tz_name):
    tz = pytz.timezone(tz_name or 'UTC')
    return utc_dt.replace(tzinfo=pytz.utc).astimezone(tz)


def event_local_to_utc(local_dt, tz_name):
    """Interprets a naive datetime as wall-clock time in tz_name and returns it as naive UTC."""
    tz = pytz.timezone(tz_name or 'UTC')
    return tz.localize(local_dt).astimezone(pytz.utc).replace(tzinfo=None)
