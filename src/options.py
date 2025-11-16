from dataclasses import dataclass
import os
import re
from typing import Optional
from durations_nlp import Duration

CALENDAR_ID_ENV = "CALENDAR_ID"
CALDAV_HOST_ENV = "CALDAV_HOST"
CALDAV_USERNAME_ENV = "CALDAV_USERNAME"
CALDAV_PASSWORD_ENV = "CALDAV_PASSWORD"

TRUENAS_HOST_ENV = "TRUENAS_HOST"
TRUENAS_HOST_VERIFY_SSL_ENV = "TRUENAS_HOST_VERIFY_SSL"
TRUENAS_API_KEY_ENV = "TRUENAS_API_KEY"

INCLUDE_SNAPSHOTS_ENV = "INCLUDE_SNAPSHOTS"
INCLUDE_SCRUBS_ENV = "INCLUDE_SCRUBS"
INCLUDE_CLOUDSYNCS_ENV = "INCLUDE_CLOUDSYNCS"
INCLUDE_CRONJOBS_ENV = "INCLUDE_CRONJOBS"

SNAPSHOTS_REGEX_ENV = "SNAPSHOTS_FILTER"
SCRUBS_REGEX_ENV = "SCRUBS_FILTER"
CLOUDSYNCS_REGEX_ENV = "CLOUDSYNCS_FILTER"
CRONJOBS_REGEX_ENV = "CRONJOBS_FILTER"

FAILURE_BACKOFF_TIME_ENV = "FAILURE_BACKOFF_TIME"
SYNC_INTERVAL_ENV = "SYNC_INTERVAL"


def parse_string(env: str, required: bool, default_value=""):
    result = os.environ.get(env, "")
    if result == "":
        if required:
            raise Exception(f"Environment variable {env} is required.")

        return default_value

    return result


def parse_bool(env: str, required: bool, default_value=False):
    result = parse_string(env, required)
    if result.lower() in ("true", "yes"):
        return True

    if result.lower() in ("false", "no"):
        return False

    if result == "":
        return default_value

    raise Exception(f"Unrecognized bool value {result}")


def compile_regex(env: str) -> Optional[re.Pattern]:
    pattern = os.environ.get(env, "")
    if pattern == "":
        return None

    return re.compile(pattern)


@dataclass
class Options:
    calendar_id: str
    caldav_host: str
    caldav_username: str
    caldav_password: str

    truenas_host: str
    truenas_host_verify_ssl: bool
    truenas_api_key: str

    include_snapshots: bool
    include_scrubs: bool
    include_cloudsyncs: bool
    include_cronjobs: bool

    snapshots_filter: Optional[re.Pattern]
    scrubs_filter: Optional[re.Pattern]
    cloudsyncs_filter: Optional[re.Pattern]
    cronjobs_filter: Optional[re.Pattern]

    failure_backoff_time: Duration
    sync_interval: Duration

    @staticmethod
    def from_env():
        calendar_id = parse_string(CALENDAR_ID_ENV, True)
        caldav_host = parse_string(CALDAV_HOST_ENV, True)
        caldav_username = parse_string(CALDAV_USERNAME_ENV, True)
        caldav_password = parse_string(CALDAV_PASSWORD_ENV, True)

        truenas_host = parse_string(TRUENAS_HOST_ENV, True)
        truenas_host_verify_ssl = parse_bool(TRUENAS_HOST_VERIFY_SSL_ENV, False, True)
        truenas_api_key = parse_string(TRUENAS_API_KEY_ENV, True)

        include_snapshots = parse_bool(INCLUDE_SNAPSHOTS_ENV, False, True)
        include_scrubs = parse_bool(INCLUDE_SCRUBS_ENV, False, True)
        include_cloudsyncs = parse_bool(INCLUDE_CLOUDSYNCS_ENV, False, True)
        include_cronjobs = parse_bool(INCLUDE_CRONJOBS_ENV, False, True)

        snapshots_filter = compile_regex(SNAPSHOTS_REGEX_ENV)
        scrubs_filter = compile_regex(SCRUBS_REGEX_ENV)
        cloudsyncs_filter = compile_regex(CLOUDSYNCS_REGEX_ENV)
        cronjobs_filter = compile_regex(CRONJOBS_REGEX_ENV)

        failure_backoff_time = Duration(parse_string(FAILURE_BACKOFF_TIME_ENV, False, "15 minutes"))
        sync_interval = Duration(parse_string(SYNC_INTERVAL_ENV, False, "1 hour"))

        return Options(calendar_id,
                       caldav_host,
                       caldav_username,
                       caldav_password,

                       truenas_host,
                       truenas_host_verify_ssl,
                       truenas_api_key,

                       include_snapshots,
                       include_scrubs,
                       include_cloudsyncs,
                       include_cronjobs,

                       snapshots_filter,
                       scrubs_filter,
                       cloudsyncs_filter,
                       cronjobs_filter,

                       failure_backoff_time,
                       sync_interval)
