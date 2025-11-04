from cron_to_ical import cron_to_ical, FREQ_MINUTELY, FREQ_HOURLY, FREQ_WEEKLY, FREQ_DAILY, FREQ_MONTHLY, FREQ_YEARLY


def test_every_minute():
    res = cron_to_ical("* * * * *")
    assert res.rrule["FREQ"] == FREQ_MINUTELY
    assert len(res.rrule) == 1


def test_every_30_minutes():
    res = cron_to_ical("0,30 * * * *")
    assert res.rrule["FREQ"] == FREQ_HOURLY
    assert res.rrule["BYMINUTE"] == [0, 30]
    assert len(res.rrule) == 2


def test_every_30_minutes_in_hour_2():
    res = cron_to_ical("0,30 2 * * *")
    assert res.rrule["FREQ"] == FREQ_DAILY
    assert res.rrule["BYMINUTE"] == [0, 30]
    assert res.rrule["BYHOUR"] == [2]
    assert len(res.rrule) == 3


def test_top_of_every_hour_in_may():
    res = cron_to_ical("0 * * 5 *")
    assert res.rrule["FREQ"] == FREQ_HOURLY
    assert res.rrule["BYMINUTE"] == [0]
    assert res.rrule["BYMONTH"] == [5]
    assert len(res.rrule) == 3


def test_every_tuesday_at_noon():
    res = cron_to_ical("0 12 * * tue")
    assert res.rrule["FREQ"] == FREQ_WEEKLY
    assert res.rrule["BYMINUTE"] == [0]
    assert res.rrule["BYHOUR"] == [12]
    assert res.rrule["BYDAY"] == ["TU"]
    assert len(res.rrule) == 4


def test_every_may_or_june_or_july_22_or_23_at_noon_on_friday():
    res = cron_to_ical("0 12 21,22 5-7 fri")
    assert res.rrule["FREQ"] == FREQ_YEARLY
    assert res.rrule["BYMINUTE"] == [0]
    assert res.rrule["BYHOUR"] == [12]
    assert res.rrule["BYMONTHDAY"] == [21, 22]
    assert res.rrule["BYMONTH"] == [5, 6, 7]
    assert res.rrule["BYDAY"] == ["FR"]
    assert len(res.rrule) == 6


def test_random_days_of_month_at_midnight():
    res = cron_to_ical("0 0 1,5,10,20,25 * *")
    assert res.rrule["FREQ"] == FREQ_MONTHLY
    assert res.rrule["BYMINUTE"] == [0]
    assert res.rrule["BYHOUR"] == [0]
    assert res.rrule["BYMONTHDAY"] == [1, 5, 10, 20, 25]
    assert len(res.rrule) == 4


def test_every_other_day_of_month_at_midnight():
    res = cron_to_ical("0 0 */2 * *")
    assert res.rrule["FREQ"] == FREQ_MONTHLY
    assert res.rrule["BYMINUTE"] == [0]
    assert res.rrule["BYHOUR"] == [0]
    assert res.rrule["BYMONTHDAY"] == [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31]
    assert len(res.rrule) == 4


def test_every_10_minutes():
    res = cron_to_ical("*/10 * * * *")
    assert res.rrule["FREQ"] == FREQ_HOURLY
    assert res.rrule["BYMINUTE"] == [0, 10, 20, 30, 40, 50]
    assert len(res.rrule) == 2
