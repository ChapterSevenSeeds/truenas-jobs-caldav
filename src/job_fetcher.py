import re
import logging
from typing import Dict, Optional, List
from truenas_api_client import JSONRPCClient, LegacyClient
from icalendar import Calendar, Event as ICalEvent
from common import ITEM_TYPE_CLOUDSYNC, ITEM_TYPE_CRONJOB, ITEM_TYPE_SCRUB, ITEM_TYPE_SNAPSHOT, create_item_uid, resolve_local_iana_timezone, schedule_to_cron_string
from cron_to_ical import FREQ_HOURLY, FREQ_MINUTELY, cron_to_ical
from options import Options

logger = logging.getLogger(__name__)


def fetch_and_filter_items(
    items_filter: Optional[re.Pattern],
    truenas_client: JSONRPCClient | LegacyClient,
    query: str,
    enabled_key: str | None,
    item_type: str,
    item_description_key: str,
) -> List[Dict]:
    """
    Fetches TrueNAS items and filters them based on the provided regex pattern.

    :param items_filter: A regular expression pattern to filter items.
    :param truenas_client: The TrueNAS API client to use for fetching item data.
    :param query: The query to use for fetching items from the TrueNAS API.
    :param enabled_key: The key to check if the item is enabled.
    :param item_type: The type of the item.
    :param item_description_key: The key for the item description.
    :return: A list of filtered, enabled items.
    """
    logger.info(f"Performing query \"{query}\" for items of type \"{item_type}\".")

    items: list[Dict] = truenas_client.call(query)  # type: ignore
    logger.info(f"Found {len(items)} items.")

    # Filter by regex if provided
    if items_filter is not None:
        logger.info(f"Filtering items with pattern \"{items_filter.pattern}\".")
        filtered_items = [x for x in items if items_filter.search(x[item_description_key]) is not None]
        logger.info(f"{len(filtered_items)} items remain after filtering.")
    else:
        filtered_items = items

    # Filter by enabled status
    enabled_items = []
    for item in filtered_items:
        if enabled_key is not None and not item[enabled_key]:
            logger.info(f"Skipping item \"{item_type}: {item[item_description_key]}\" because it is disabled.")
            continue
        enabled_items.append(item)

    return enabled_items


def create_ical_event(
    item: Dict,
    item_type: str,
    item_description_key: str,
    item_summary_prefix: str,
    iana_timezone: str | None,
) -> ICalEvent:
    """
    Creates an iCal event from a TrueNAS item.

    :param item: The TrueNAS item data.
    :param item_type: The type of the item.
    :param item_description_key: The key for the item description.
    :param item_summary_prefix: The prefix for the item summary.
    :param iana_timezone: The IANA timezone for the event.
    :return: An iCalendar Event object.
    """
    item_summary = f"{item_summary_prefix}{item[item_description_key]}"
    logger.info(f"Creating event for item: \"{item_summary}\".")

    cron_str = schedule_to_cron_string(item["schedule"])
    logger.info(f"Found CRON expression {cron_str}.")

    ical = cron_to_ical(cron_str, iana_timezone=iana_timezone)
    logger.info(f"Resulting ICAL object: {ical}")

    if ical.rrule["FREQ"] in (FREQ_HOURLY, FREQ_MINUTELY):
        logger.warning("Hourly and minutely FREQs might not be supported by some calendars!")

    event_uid = create_item_uid(item_type, item['id'])

    # Create iCalendar event
    event = ICalEvent()
    event.add('uid', event_uid)
    event.add('summary', item_summary)
    event.add('dtstart', ical.start)
    event.add('dtend', ical.end)
    event.add('rrule', ical.rrule)

    return event


def fetch_all_jobs(options: Options, truenas_client: JSONRPCClient | LegacyClient) -> Calendar:
    """
    Fetches all TrueNAS jobs and converts them to an iCalendar object.

    :param options: The parsed options for the application.
    :param truenas_client: The TrueNAS client to use for fetching job data.
    :return: An iCalendar Calendar object containing all job events.
    """
    logger.info("Fetching TrueNAS jobs and converting to iCalendar format.")

    # Create calendar
    cal = Calendar()
    cal.add('prodid', '-//TrueNAS Jobs Calendar//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'TrueNAS Jobs - {options.calendar_name}')
    iana_timezone = resolve_local_iana_timezone()
    cal.add('x-wr-timezone', iana_timezone or 'UTC')

    # Fetch and create events for each job type
    job_configs = []

    if options.include_snapshots:
        logger.info("Including snapshots...")
        job_configs.append({
            'filter': options.snapshots_filter,
            'query': "pool.snapshottask.query",
            'enabled_key': "enabled",
            'item_type': ITEM_TYPE_SNAPSHOT,
            'description_key': "dataset",
            'item_summary_prefix': options.snapshots_suffix
        })

    if options.include_scrubs:
        logger.info("Including scrubs...")
        job_configs.append({
            'filter': options.scrubs_filter,
            'query': "pool.scrub.query",
            'enabled_key': "enabled",
            'item_type': ITEM_TYPE_SCRUB,
            'description_key': "pool_name",
            'item_summary_prefix': options.scrubs_suffix
        })

    if options.include_cloudsyncs:
        logger.info("Including cloudsync tasks...")
        job_configs.append({
            'filter': options.cloudsyncs_filter,
            'query': "cloudsync.query",
            'enabled_key': "enabled",
            'item_type': ITEM_TYPE_CLOUDSYNC,
            'description_key': "description",
            'item_summary_prefix': options.cloudsyncs_suffix
        })

    if options.include_cronjobs:
        logger.info("Including cronjobs...")
        job_configs.append({
            'filter': options.cronjobs_filter,
            'query': "cronjob.query",
            'enabled_key': "enabled",
            'item_type': ITEM_TYPE_CRONJOB,
            'description_key': "description",
            'item_summary_prefix': options.cronjobs_suffix
        })

    # Fetch items and create events
    for config in job_configs:
        items = fetch_and_filter_items(
            config['filter'],
            truenas_client,
            config['query'],
            config['enabled_key'],
            config['item_type'],
            config['description_key'],
        )

        for item in items:
            event = create_ical_event(item, config['item_type'], config['description_key'], config['item_summary_prefix'], iana_timezone)
            cal.add_component(event)

    logger.info(f"Calendar created with {len(cal.subcomponents)} events.")
    return cal
