# https://www.truenas.com/docs/api/scale_websocket_api.html#cronjob
# https://caldav.readthedocs.io/stable/tutorial.html
# https://radicale.org/v3.html

ITEM_TYPE_SCRUB = "Scrub"
ITEM_TYPE_SNAPSHOT = "Snapshot"
ITEM_TYPE_CLOUDSYNC = "CloudSync"
ITEM_TYPE_CRONJOB = "CronJob"

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
    return f"truenas-{prefix.lower()}-{item_id}"