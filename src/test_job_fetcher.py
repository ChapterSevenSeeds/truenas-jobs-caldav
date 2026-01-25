"""
Integration test for job_fetcher module.
Tests the iCalendar generation logic without requiring a live TrueNAS instance.
"""
import pytest
from unittest.mock import Mock, MagicMock
from job_fetcher import fetch_and_filter_items, create_ical_event, fetch_all_jobs
from options import Options
from icalendar import Calendar
import re


def create_mock_truenas_client():
    """Create a mock TrueNAS client."""
    mock_client = MagicMock()
    
    # Mock snapshot data
    mock_client.call = Mock(side_effect=lambda query: {
        "pool.snapshottask.query": [
            {
                "id": 1,
                "enabled": True,
                "dataset": "tank/data",
                "schedule": {
                    "minute": "0",
                    "hour": "2",
                    "dom": "*",
                    "month": "*",
                    "dow": "*"
                }
            },
            {
                "id": 2,
                "enabled": False,
                "dataset": "tank/backup",
                "schedule": {
                    "minute": "0",
                    "hour": "3",
                    "dom": "*",
                    "month": "*",
                    "dow": "*"
                }
            }
        ],
        "pool.scrub.query": [
            {
                "id": 3,
                "enabled": True,
                "pool_name": "tank",
                "schedule": {
                    "minute": "0",
                    "hour": "0",
                    "dom": "1",
                    "month": "*",
                    "dow": "*"
                }
            }
        ],
        "cloudsync.query": [
            {
                "id": 4,
                "enabled": True,
                "description": "Backup to S3",
                "schedule": {
                    "minute": "30",
                    "hour": "1",
                    "dom": "*",
                    "month": "*",
                    "dow": "0"
                }
            }
        ],
        "cronjob.query": [
            {
                "id": 5,
                "enabled": True,
                "description": "Daily cleanup",
                "schedule": {
                    "minute": "0",
                    "hour": "4",
                    "dom": "*",
                    "month": "*",
                    "dow": "*"
                }
            }
        ]
    }.get(query, []))
    
    return mock_client


def test_fetch_and_filter_items_enabled_only():
    """Test that only enabled items are returned."""
    mock_client = create_mock_truenas_client()
    
    items = fetch_and_filter_items(
        items_filter=None,
        truenas_client=mock_client,
        query="pool.snapshottask.query",
        enabled_key="enabled",
        item_type="Snapshot",
        item_description_key="dataset"
    )
    
    # Should only return the enabled snapshot (id=1)
    assert len(items) == 1
    assert items[0]["id"] == 1
    assert items[0]["dataset"] == "tank/data"


def test_fetch_and_filter_items_with_regex():
    """Test filtering items with a regex pattern."""
    mock_client = create_mock_truenas_client()
    
    # Filter for datasets containing "data"
    pattern = re.compile("data")
    items = fetch_and_filter_items(
        items_filter=pattern,
        truenas_client=mock_client,
        query="pool.snapshottask.query",
        enabled_key="enabled",
        item_type="Snapshot",
        item_description_key="dataset"
    )
    
    # Should only return the "tank/data" snapshot
    assert len(items) == 1
    assert items[0]["dataset"] == "tank/data"


def test_create_ical_event():
    """Test creating an iCalendar event from a TrueNAS item."""
    item = {
        "id": 1,
        "dataset": "tank/data",
        "schedule": {
            "minute": "0",
            "hour": "2",
            "dom": "*",
            "month": "*",
            "dow": "*"
        }
    }
    
    event = create_ical_event(item, "Snapshot", "dataset", iana_timezone=None)
    
    # Verify event properties
    assert event['uid'] == "truenas-snapshot-1"
    assert event['summary'] == "Snapshot: tank/data"
    assert 'dtstart' in event
    assert 'dtend' in event
    assert 'rrule' in event
    assert event['rrule']['FREQ'] == 'DAILY'


def test_fetch_all_jobs():
    """Test fetching all jobs and creating a complete calendar."""
    mock_client = create_mock_truenas_client()
    
    options = Options(
        calendar_name="test-calendar",
        http_port=8080,
        truenas_host="test.local",
        truenas_host_verify_ssl=False,
        truenas_api_key="test-key",
        include_snapshots=True,
        include_scrubs=True,
        include_cloudsyncs=True,
        include_cronjobs=True,
        snapshots_filter=None,
        scrubs_filter=None,
        cloudsyncs_filter=None,
        cronjobs_filter=None
    )
    
    cal = fetch_all_jobs(options, mock_client)
    
    # Verify calendar type and properties
    assert isinstance(cal, Calendar)
    assert cal['prodid'] == '-//TrueNAS Jobs Calendar//EN'
    assert cal['version'] == '2.0'
    
    # Should have 4 events (1 snapshot, 1 scrub, 1 cloudsync, 1 cronjob)
    # The disabled snapshot should not be included
    events = [comp for comp in cal.subcomponents if comp.name == 'VEVENT']
    assert len(events) == 4
    
    # Verify event summaries
    summaries = [str(event['summary']) for event in events]
    assert "Snapshot: tank/data" in summaries
    assert "Scrub: tank" in summaries
    assert "CloudSync: Backup to S3" in summaries
    assert "CronJob: Daily cleanup" in summaries


def test_fetch_all_jobs_selective_inclusion():
    """Test that job types can be selectively included."""
    mock_client = create_mock_truenas_client()
    
    options = Options(
        calendar_name="test-calendar",
        http_port=8080,
        truenas_host="test.local",
        truenas_host_verify_ssl=False,
        truenas_api_key="test-key",
        include_snapshots=True,
        include_scrubs=False,
        include_cloudsyncs=False,
        include_cronjobs=False,
        snapshots_filter=None,
        scrubs_filter=None,
        cloudsyncs_filter=None,
        cronjobs_filter=None
    )
    
    cal = fetch_all_jobs(options, mock_client)
    
    # Should only have 1 event (snapshot)
    events = [comp for comp in cal.subcomponents if comp.name == 'VEVENT']
    assert len(events) == 1
    assert str(events[0]['summary']) == "Snapshot: tank/data"


def test_ical_output_validity():
    """Test that the generated iCalendar output is valid."""
    mock_client = create_mock_truenas_client()
    
    options = Options(
        calendar_name="test-calendar",
        http_port=8080,
        truenas_host="test.local",
        truenas_host_verify_ssl=False,
        truenas_api_key="test-key",
        include_snapshots=True,
        include_scrubs=True,
        include_cloudsyncs=True,
        include_cronjobs=True,
        snapshots_filter=None,
        scrubs_filter=None,
        cloudsyncs_filter=None,
        cronjobs_filter=None
    )
    
    cal = fetch_all_jobs(options, mock_client)
    
    # Convert to iCalendar string
    ical_string = cal.to_ical().decode('utf-8')
    
    # Verify basic iCalendar structure
    assert 'BEGIN:VCALENDAR' in ical_string
    assert 'END:VCALENDAR' in ical_string
    assert 'VERSION:2.0' in ical_string
    assert 'PRODID:-//TrueNAS Jobs Calendar//EN' in ical_string
    
    # Should have VEVENT blocks for each job
    assert ical_string.count('BEGIN:VEVENT') == 4
    assert ical_string.count('END:VEVENT') == 4
    
    # Verify event UIDs are present
    assert 'truenas-snapshot-1' in ical_string
    assert 'truenas-scrub-3' in ical_string
    assert 'truenas-cloudsync-4' in ical_string
    assert 'truenas-cronjob-5' in ical_string
