import pytz


def event_local_date(utc_dt, tz_name):
    tz = pytz.timezone(tz_name or 'UTC')
    return utc_dt.replace(tzinfo=pytz.utc).astimezone(tz).date()
