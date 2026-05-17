from dataclasses import dataclass
import os
import re
from typing import Optional

CALENDAR_NAME_ENV = "CALENDAR_NAME"
HTTP_PORT_ENV = "HTTP_PORT"

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

SNAPSHOTS_SUMMARY_PREFIX_ENV = "SNAPSHOTS_SUMMARY_PREFIX"
SCRUBS_SUMMARY_PREFIX_ENV = "SCRUBS_SUMMARY_PREFIX"
CLOUDSYNCS_SUMMARY_PREFIX_ENV = "CLOUDSYNCS_SUMMARY_PREFIX"
CRONJOBS_SUMMARY_PREFIX_ENV = "CRONJOBS_SUMMARY_PREFIX"

# Regex for validating calendar name - only allow alphanumeric, hyphens, and underscores
CALENDAR_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')


def parse_string(env: str, required: bool, default_value="", allow_empty=False):
    result = os.environ.get(env, None)
    is_empty = result == ""
    is_undefined = result is None

    if is_undefined:
        if required:
            raise Exception(f"Environment variable {env} is required.")

        # If undefined but not required, use the default.
        return default_value

    if is_empty:
        # 1. Optional but can't be empty: return default
        # 2. Optional and can be empty: return empty string
        # 3. Required but can be empty: return empty string
        # 4. Required and can't be empty: raise exception
        
        if required and not allow_empty:
            # Case 4
            raise Exception(f"Environment variable {env} is required and cannot be empty.")
        
        if allow_empty:
            # Cases 2 and 3
            return ""
        
        # Case 1
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


def parse_int(env: str, required: bool, default_value=0):
    result = parse_string(env, required, str(default_value))
    if result == str(default_value):
        return default_value

    try:
        return int(result)
    except ValueError:
        raise Exception(f"Invalid integer value for {env}: {result}")


def compile_regex(env: str) -> Optional[re.Pattern]:
    pattern = os.environ.get(env, "")
    if pattern == "":
        return None

    return re.compile(pattern)


@dataclass
class Options:
    calendar_name: str
    http_port: int

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

    snapshots_prefix: str
    scrubs_prefix: str
    cloudsyncs_prefix: str
    cronjobs_prefix: str

    @staticmethod
    def from_env():
        calendar_name = parse_string(CALENDAR_NAME_ENV, True)

        # Validate calendar name for security
        if not CALENDAR_NAME_PATTERN.match(calendar_name):
            raise Exception(
                f"Invalid CALENDAR_NAME '{calendar_name}'. "
                f"Only alphanumeric characters, hyphens, and underscores are allowed."
            )

        http_port = parse_int(HTTP_PORT_ENV, False, 8080)

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

        snapshots_prefix = parse_string(SNAPSHOTS_SUMMARY_PREFIX_ENV, False, "Snapshot: ", allow_empty=True)
        scrubs_prefix = parse_string(SCRUBS_SUMMARY_PREFIX_ENV, False, "Scrub: ", allow_empty=True)
        cloudsyncs_prefix = parse_string(CLOUDSYNCS_SUMMARY_PREFIX_ENV, False, "CloudSync: ", allow_empty=True)
        cronjobs_prefix = parse_string(CRONJOBS_SUMMARY_PREFIX_ENV, False, "CronJob: ", allow_empty=True)

        return Options(calendar_name,
                       http_port,

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

                       snapshots_prefix,
                       scrubs_prefix,
                       cloudsyncs_prefix,
                       cronjobs_prefix)
