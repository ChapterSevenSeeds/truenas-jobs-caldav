# https://www.truenas.com/docs/api/scale_websocket_api.html#cronjob
# https://caldav.readthedocs.io/stable/tutorial.html
# https://radicale.org/v3.html

from datetime import datetime
import logging
import time
from zoneinfo import ZoneInfo, available_timezones

from dateutil import tz


ITEM_TYPE_SCRUB = "Scrub"
ITEM_TYPE_SNAPSHOT = "Snapshot"
ITEM_TYPE_CLOUDSYNC = "CloudSync"
ITEM_TYPE_CRONJOB = "CronJob"

logger = logging.getLogger(__name__)


def schedule_to_cron_string(schedule: dict[str, str]) -> str:
    """
    Converts a schedule dictionary to a CRON string.

    :param schedule: The schedule dict.
    :type schedule: dict[str, str]
    :return: The CRON string representation of the schedule.
    :rtype: str
    """
    return f"{schedule.get("minute", "0")} {schedule["hour"]} {schedule["dom"]} {schedule["month"]} {schedule["dow"]}"


def create_item_uid(prefix: str, item_id: int) -> str:
    """Creates a unique identifier for a TrueNAS item.
    :param prefix: The item type prefix.
    :param item_id: The unique item ID.
    :return: A unique identifier string.
    """

    return f"truenas-{prefix.lower()}-{item_id}"


def resolve_local_iana_timezone() -> str | None:
    """Best-effort mapping from the system's local timezone to an IANA timezone.

    This is based on matching current UTC offset + DST rule against known IANA zones.
    It is necessarily approximate (multiple IANA zones can share offset/DST).
    """

    local_tz = tz.gettz(time.tzname[time.daylight])
    if local_tz is None:
        logger.warning("Could not determine the local timezone. Your calendar events may show at incorrect times.")
        return None

    reference = datetime.now(local_tz)
    local_offset = reference.utcoffset()
    local_dst = reference.dst()

    candidates: list[str] = []
    for candidate_zone_str in sorted(available_timezones()):
        candidate_zone = ZoneInfo(candidate_zone_str)
        candidate_reference = datetime.now(candidate_zone)
        if local_offset == candidate_reference.utcoffset() and local_dst == candidate_reference.dst():
            candidates.append(candidate_zone_str)

    if len(candidates) == 0:
        logger.warning("Could not map local timezone to any IANA timezone. Your calendar events may show at incorrect times.")
        return None

    return candidates[0]
