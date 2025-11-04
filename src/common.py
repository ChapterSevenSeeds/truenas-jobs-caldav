# https://www.truenas.com/docs/api/scale_websocket_api.html#cronjob
# https://caldav.readthedocs.io/stable/tutorial.html
# https://radicale.org/v3.html

ITEM_TYPE_SCRUB = "Scrub"
ITEM_TYPE_SNAPSHOT = "Snapshot"
ITEM_TYPE_CLOUDSYNC = "CloudSync"
ITEM_TYPE_SMART_TEST = "SMART Test"
ITEM_TYPE_CRONJOB = "CronJob"

def schedule_to_cron_string(schedule: dict[str, str]) -> str:
    return f"{schedule.get("minute", "0")} {schedule["hour"]} {schedule["dom"]} {schedule["month"]} {schedule["dow"]}"

def create_item_uid(prefix: str, item_id: int) -> str:
    return f"truenas-{prefix.lower()}-{item_id}"

def parse_item_type_from_uid(uid: str) -> str | None:
    parts = uid.split("-")
    if len(parts) >= 3 and parts[0] == "truenas":
        return parts[1].lower()
    return None