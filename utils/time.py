from datetime import datetime, timedelta, date
import time
import calendar


def bj_now():
    utc_now = datetime.utcnow()

    return utc_now+timedelta(hours=8)


def get_next_day(_date):
    return _date + timedelta(days=1)


def this_week_start():
    now = bj_now()
    return now - timedelta(days=now.weekday())


def get_week_start(_date=None):
    if _date is None:
        _date = bj_now()

    return _date - timedelta(days=_date.weekday())


def get_next_week_start(_date=None):
    if _date is None:
        _date = bj_now()
    return _date - timedelta(days=_date.weekday()) + timedelta(days=7)


def get_apm(am='a', pm='p', now=None):
    """ 获取am or pm """
    if now is None:
        now = bj_now()

    # print(now.hour)
    if now.hour >= 12:
        return pm
    return am


def get_weekday(_date):
    d = [ '星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日',]
    return d[_date.weekday()]


def get_datetime(_date, t="a"):
    return datetime(year=_date.year, month=_date.month, day=_date.day, hour=13 if t == "a" else 23)


def get_datetime_display(_time, fmt="%Y-%m-%d %H:%M:%S"):
    if isinstance(_time, int):
        if _time > 0:
            _time = datetime.fromtimestamp(_time)

    if _time:
        return _time.strftime(fmt)
    return ""


def get_timestamp(_date=None, base=1970):
    # _date 本地时间
    dt = calendar.timegm((base, 1, 1, 0, 0, 0, 0, 0, 0))
    if _date:
        _t = time.mktime(_date.timetuple())
    else:
        _t = time.time()

    return int(_t-dt)

def get_timestamp_2000(_date=None):
    # _date 本地时间
    return get_timestamp(_date, base=2000)
