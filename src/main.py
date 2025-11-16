import re
import time
from typing import Dict, Optional
from truenas_api_client import Client, JSONRPCClient, LegacyClient
from caldav.davclient import DAVClient, get_davclient
from caldav.collection import Calendar
from caldav.calendarobjectresource import Event
from common import ITEM_TYPE_CLOUDSYNC, ITEM_TYPE_CRONJOB, ITEM_TYPE_SCRUB, ITEM_TYPE_SNAPSHOT, create_item_uid, parse_item_type_from_uid, schedule_to_cron_string
from cron_to_ical import FREQ_HOURLY, FREQ_MINUTELY, cron_to_ical
from options import Options
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def create_events(
    items_filter: Optional[re.Pattern],
    truenas_client: JSONRPCClient | LegacyClient,
    events: list[Event],
    calendar: Calendar,
    query: str,
    enabled_key: str | None,
    item_type: str,
    item_description_key: str
) -> set[str]:
    """
    Generates calendar events for TrueNAS items of a given type.
    
    :param items_filter: A regular expression pattern to filter items.
    :type items_filter: Optional[re.Pattern]
    :param truenas_client: The TrueNAS API client to use for fetching item data.
    :type truenas_client: JSONRPCClient | LegacyClient
    :param events: A list of existing calendar events.
    :type events: list[Event]
    :param calendar: The calendar to which events will be added.
    :type calendar: Calendar
    :param query: The query to use for fetching items from the TrueNAS API.
    :type query: str
    :param enabled_key: The key to check if the item is enabled.
    :type enabled_key: str | None
    :param item_type: The type of the item.
    :type item_type: str
    :param item_description_key: The key for the item description.
    :type item_description_key: str
    :return: A set of event UIDs that were created or updated.
    :rtype: set[str]
    """
    logger.info(f"Performing query \"{query}\" for events with summary prefix \"{item_type}\".")

    items: list[Dict] = truenas_client.call(query)  # type: ignore
    logger.info(f"Found {len(items)} items.")

    event_uids_saved: set[str] = set()

    if items_filter is not None:
        logger.info(f"Filtering items with pattern \"{items_filter.pattern}\".")
        filtered_items = [x for x in items if items_filter.search(x[item_description_key]) is not None]
        logger.info(f"{len(filtered_items)} items remain after filtering.")
    else:
        filtered_items = items

    for item in filtered_items:
        item_summary = f"{item_type}: {item[item_description_key]}"
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

        event_uid = create_item_uid(item_type, item['id'])
        previous_events: list[Event] = [x for x in events if x.component.uid == event_uid]

        event_uids_saved.add(event_uid)

        if len(previous_events) > 0:
            logger.info("Updating previously saved event...")
            previous_event = previous_events[0]
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

    return event_uids_saved


def perform_sync(options: Options, dav_client: DAVClient, truenas_client: JSONRPCClient | LegacyClient):
    """
    Performs synchronization of TrueNAS recurring jobs with a CalDAV server.
    
    :param options: The parsed options for the synchronization.
    :type options: Options
    :param dav_client: The CalDAV client to use for interacting with the calendar.
    :type dav_client: DAVClient
    :param truenas_client: The TrueNAS client to use for fetching job data.
    :type truenas_client: JSONRPCClient | LegacyClient
    """
    
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

    def filter_events_by_type(item_type: str) -> list[Event]:
        return [x for x in all_events if parse_item_type_from_uid(x.component.uid) == item_type.lower()]

    event_uids_saved: set[str] = set()

    # Sync all the things.

    if not options.include_snapshots:
        logger.info("Ignoring snapshots...")
    else:
        logger.info("Syncing snapshots...")
        event_uids_saved = event_uids_saved.union(
            create_events(
                options.snapshots_filter,
                truenas_client,
                filter_events_by_type(ITEM_TYPE_SNAPSHOT),
                truenas_calendar,
                "pool.snapshottask.query",
                "enabled",
                ITEM_TYPE_SNAPSHOT,
                "dataset"))

    if not options.include_scrubs:
        logger.info("Ignoring scrubs...")
    else:
        logger.info("Syncing scrubs...")
        event_uids_saved = event_uids_saved.union(
            create_events(
                options.scrubs_filter,
                truenas_client,
                filter_events_by_type(ITEM_TYPE_SCRUB),
                truenas_calendar,
                "pool.scrub.query",
                "enabled",
                ITEM_TYPE_SCRUB,
                "pool_name"))

    if not options.include_cloudsyncs:
        logger.info("Ignoring cloudsync tasks...")
    else:
        logger.info("Syncing cloudsync tasks...")
        event_uids_saved = event_uids_saved.union(
            create_events(
                options.cloudsyncs_filter,
                truenas_client,
                filter_events_by_type(ITEM_TYPE_CLOUDSYNC),
                truenas_calendar,
                "cloudsync.query",
                "enabled",
                ITEM_TYPE_CLOUDSYNC,
                "description"))

    if not options.include_cronjobs:
        logger.info("Ignoring cronjobs...")
    else:
        logger.info("Syncing cronjobs...")
        event_uids_saved = event_uids_saved.union(
            create_events(
                options.cronjobs_filter,
                truenas_client,
                filter_events_by_type(ITEM_TYPE_CRONJOB),
                truenas_calendar,
                "cronjob.query",
                "enabled",
                ITEM_TYPE_CRONJOB,
                "description"))

    # Remove stale events
    logger.info("Sync complete, removing stale events...")
    for event in (event for event in all_events if event.component.uid not in event_uids_saved):
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
