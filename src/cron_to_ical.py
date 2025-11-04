import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence, Union
from cron_converter import Cron
from zoneinfo import ZoneInfo, available_timezones
from dateutil import tz

logger = logging.getLogger(__name__)

FREQ_MONTHLY = "MONTHLY"
FREQ_YEARLY = "YEARLY"
FREQ_WEEKLY = "WEEKLY"
FREQ_DAILY = "DAILY"
FREQ_HOURLY = "HOURLY"
FREQ_MINUTELY = "MINUTELY"


def dow_to_str(dow: int):
    """
    Converts a day of the week integer to the iCal equivalent.
    """
    return {0: "SU", 1: "MO", 2: "TU", 3: "WE", 4: "TH", 5: "FR", 6: "SA"}[dow]


@dataclass
class ICalResult:
    start: datetime
    end: datetime
    rrule: dict[str, Union[str, Sequence[Union[int, str]]]]


def cron_to_ical(cron: str) -> ICalResult:
    """
    Generates an abstract iCal thing according to a CRON expression.

    Currently, this handles all intervals literally (using a larger FREQ with evenly spaced BY* filters). This works fine because the cron_converter package provides the next start datetime for a CRON, aligning everything properly.
    TODO: Change this to properly handle CRON intervals.
    """
    c = Cron(cron)
    (minute, hour, dom, month, dow) = c.parts

    if not minute or not hour or not dom or not month or not dow:
        raise Exception(f"Invalid CRON expression {cron}")

    frequency = ""

    # Every minute requires a minutely freq.
    if minute.is_full():
        frequency = FREQ_MINUTELY
    # Every hour but at certain minutes requires an hourly freq.
    elif hour.is_full():
        frequency = FREQ_HOURLY
    # If this CRON has minute and hour parts, and if we are to run every day of the week and month, then we need a daily freq.
    elif dow.is_full() and dom.is_full():
        frequency = FREQ_DAILY
    # If every day of the month but specific days of the week, then we need a weekly freq.
    elif not dow.is_full() and dom.is_full():
        frequency = FREQ_WEEKLY
    # If every day of the week but specific days of the month, then we need a monthly freq.
    elif dow.is_full() and not dom.is_full():
        frequency = FREQ_MONTHLY
    # If we get to this next condition, then we have specific days of both the week and month. If we are to do that every month, then we need a monthly freq.
    elif month.is_full():
        frequency = FREQ_MONTHLY
    # Otherwise, just go with yearly.
    else:
        frequency = FREQ_YEARLY

    options: dict[str, Union[str, Sequence[Union[int, str]]]] = {
        'FREQ': frequency,
    }

    if not minute.is_full():
        options['BYMINUTE'] = minute.to_list()
    if not hour.is_full():
        options['BYHOUR'] = hour.to_list()
    if not dow.is_full():
        options['BYDAY'] = list(map(dow_to_str, dow.to_list()))
    if not dom.is_full():
        options['BYMONTHDAY'] = dom.to_list()
    if not month.is_full():
        options['BYMONTH'] = month.to_list()

    # Use the local timezone here for the cron schedule to grab the next start datetime.
    now = datetime.now(tz.gettz(time.tzname[time.daylight]))
    schedule = c.schedule(start_date=now)
    next_start = schedule.prev()

    # Now we need to convert the timezone info from whatever it is to an IANA timezone.
    # Go grab the first matching timezone with the same offset and dst rules.
    zone_list = sorted(available_timezones())
    candidates: list[str] = []
    for candidate_zone_str in zone_list:
        candidate_zone = ZoneInfo(candidate_zone_str)
        local_tz_offset = now.utcoffset()
        local_tz_dst = now.dst()

        # Compare offsets, being careful about None results
        if local_tz_offset == candidate_zone.utcoffset(datetime.now()) and local_tz_dst == candidate_zone.dst(datetime.now()):
            candidates.append(candidate_zone_str)

    if len(candidates) > 0:
        # If we found candidates, just use the first one.
        iana_tz = sorted(candidates)[0]
        next_start = next_start.replace(tzinfo=ZoneInfo(iana_tz))
    else:
        logger.warning(f"Could not find IANA timezone for offset {now.utcoffset()} and dst {now.dst()} - using original timezone info. Your calendar may be incorrect!")

    return ICalResult(next_start, next_start, options)
