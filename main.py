from datetime import timezone
import time
from truenas_api_client import Client, JSONRPCClient, LegacyClient
from caldav.davclient import DAVClient, get_davclient
from caldav.collection import Calendar
from caldav.calendarobjectresource import Event
from cron_to_ical import FREQ_HOURLY, FREQ_MINUTELY, cron_to_ical
from options import Options
import logging

logger = logging.getLogger(__name__)

# https://www.truenas.com/docs/api/scale_websocket_api.html#cronjob
# https://caldav.readthedocs.io/stable/tutorial.html
# https://radicale.org/v3.html


def schedule_to_cron_string(schedule: dict[str, str]) -> str:
    return f"{schedule.get("minute", "0")} {schedule["hour"]} {schedule["dom"]} {schedule["month"]} {schedule["dow"]}"

def create_item_uid(prefix: str, item_id: int) -> str:
    return f"truenas-{prefix.lower()}-{item_id}"

def create_events(
    truenas_client: JSONRPCClient | LegacyClient,
    events: list[Event],
    calendar: Calendar,
    query: str,
    enabled_key: str | None,
    summary_prefix: str,
    summary_suffix_key: str
):
    logger.info(f"Performing query \"{query}\" for events with summary prefix \"{summary_prefix}\".")

    items = truenas_client.call(query)
    logger.info(f"Found {len(items)} items.")  # type:ignore
    for item in items:  # type:ignore
        item_summary = f"{summary_prefix}: {item[summary_suffix_key]}"
        logger.info(f"Found item: \"{item_summary}\".")

        if enabled_key is not None and not item[enabled_key]:
            logger.info(f"Skipping item \"{item_summary}\" because it is disabled.")
            continue

        cron_str = schedule_to_cron_string(item["schedule"])
        logger.info(f"Found CRON expression {cron_str}.")

        ical = cron_to_ical(cron_str)
        logger.info(f"Resulting ICAL object: {ical}")

        if ical.rrule["FREQ"] in (FREQ_HOURLY, FREQ_MINUTELY):
            logger.warning("Hourly and minutely FREQs might not be supported by some calendars!")

        event_uid = create_item_uid(summary_prefix, item['id'])
        previous_events: list[Event] = list(filter(lambda x: x.component.uid == event_uid, events))

        if len(previous_events) > 0:
            logger.info("Updating previously saved event...")
            previous_event = previous_events[0]
            events.remove(previous_event)
            previous_event.component.dtstart = ical.start
            previous_event.component.dtend = ical.start
            previous_event.component.rrule = ical.rrule
            previous_event.component.summary = item_summary
            previous_event.save(only_this_recurrence=False, all_recurrences=True, no_create=True)
            logger.info("Previously saved event successfully updated...")
        else:
            logger.info("Saving event to calendar...")
            calendar.save_event(
                dtstart=ical.start,
                dtend=ical.end,
                rrule=ical.rrule,
                summary=item_summary,
                uid=event_uid,
            )
            logger.info(f"Event successfully saved to calendar.")


def perform_sync(options: Options, dav_client: DAVClient, truenas_client: JSONRPCClient | LegacyClient):
    logger.info("Starting sync of recurring TrueNAS jobs with caldav server.")

    my_principal = dav_client.principal()

    # Go find the corresponding calendar
    truenas_calendar: Calendar | None = None
    for cal in my_principal.calendars():
        if cal.id != options.calendar_id:
            continue

        truenas_calendar = cal

    # Create one if it doesn't exist
    if truenas_calendar is None:
        logger.info("TrueNAS jobs calendar not found. One will be created.")
        truenas_calendar = my_principal.make_calendar("TrueNAS Jobs", options.calendar_id)
    else:
        logger.info("Found previous TrueNAS jobs calendar.")

    all_events = truenas_calendar.events()

    # Sync all the things.

    if not options.include_snapshots:
        logger.info("Ignoring snapshots...")
    else:
        logger.info("Syncing snapshots...")
        create_events(truenas_client, all_events, truenas_calendar, "pool.snapshottask.query", "enabled", "Snapshot", "dataset")

    if not options.include_scrubs:
        logger.info("Ignoring scrubs...")
    else:
        logger.info("Syncing scrubs...")
        create_events(truenas_client, all_events, truenas_calendar, "pool.scrub.query", "enabled", "Scrub", "pool_name")

    if not options.include_cloudsyncs:
        logger.info("Ignoring cloudsync tasks...")
    else:
        logger.info("Syncing cloudsync tasks...")
        create_events(truenas_client, all_events, truenas_calendar, "cloudsync.query", "enabled", "CloudSync", "description")

    if not options.include_smart_tests:
        logger.info("Ignoring SMART tests...")
    else:
        logger.info("Syncing SMART tests...")
        create_events(truenas_client, all_events, truenas_calendar, "smart.test.query", None, "SMART", "desc")

    if not options.include_cronjobs:
        logger.info("Ignoring cronjobs...")
    else:
        logger.info("Syncing cronjobs...")
        create_events(truenas_client, all_events, truenas_calendar, "cronjob.query", "enabled", "CRON", "description")

    # Remove stale events
    logger.info("Sync complete, removing stale events...")
    for event in all_events:
        logger.info(f"Removing stale event with UID {event.component.uid}.")
        event.delete()


def main():
    options = Options.from_env()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',)

    while True:
        try:
            while True:
                with get_davclient(url=f"http://{options.caldav_host}", username=options.caldav_username, password=options.caldav_password) as client:
                    logger.info("Successfully connected to caldav server.")

                    with Client(uri=f"wss://{options.truenas_host}/api/current", verify_ssl=options.truenas_host_verify_ssl) as c:
                        login_result = c.call("auth.login_with_api_key", options.truenas_api_key)

                        if not login_result:
                            raise Exception("Failed to authenticate with TrueNAS.")

                        logger.info("Successfully logged into TrueNAS.")

                        perform_sync(options, client, c)

                logger.info(f"Sync finished successfully. Sleeping for {options.sync_interval}.")
                time.sleep(options.sync_interval.seconds)
        except Exception as e:
            logger.error(f"Error encountered at root loop: {e}")
            logger.error(f"Sleeping for {options.failure_backoff_time} before trying again.")
            time.sleep(options.failure_backoff_time.seconds)


if __name__ == "__main__":
    main()
