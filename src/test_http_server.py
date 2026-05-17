from unittest.mock import Mock, patch, MagicMock
from http_server import create_app
from options import Options
from icalendar import Calendar


def create_mock_options():
    """Create a mock Options object for testing."""
    return Options(
        calendar_name="test-calendar",
        http_port=8080,
        truenas_host="truenas.local",
        truenas_host_verify_ssl=False,
        truenas_api_key="test-api-key",
        include_snapshots=True,
        include_scrubs=True,
        include_cloudsyncs=True,
        include_cronjobs=True,
        snapshots_filter=None,
        scrubs_filter=None,
        cloudsyncs_filter=None,
        cronjobs_filter=None,
        snapshots_suffix="",
        scrubs_suffix="",
        cloudsyncs_suffix="",
        cronjobs_suffix="",
    )


def test_health_check_endpoint():
    """Test that the health check endpoint returns a 200 status."""
    options = create_mock_options()
    app = create_app(options)
    client = app.test_client()

    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}


@patch('http_server.Client')
@patch('http_server.fetch_all_jobs')
def test_calendar_endpoint_success(mock_fetch_all_jobs, mock_client):
    """Test that the calendar endpoint returns a valid iCalendar."""
    options = create_mock_options()
    app = create_app(options)
    client = app.test_client()

    # Mock TrueNAS client
    mock_truenas_client = MagicMock()
    mock_truenas_client.__enter__ = Mock(return_value=mock_truenas_client)
    mock_truenas_client.__exit__ = Mock(return_value=False)
    mock_truenas_client.call.return_value = True  # Successful authentication
    mock_client.return_value = mock_truenas_client

    # Mock calendar creation
    mock_calendar = Calendar()
    mock_calendar.add('prodid', '-//Test Calendar//EN')
    mock_calendar.add('version', '2.0')
    mock_fetch_all_jobs.return_value = mock_calendar

    response = client.get('/test-calendar')

    assert response.status_code == 200
    assert 'text/calendar' in response.content_type
    assert 'charset=utf-8' in response.content_type
    assert 'BEGIN:VCALENDAR' in response.data.decode('utf-8')
    assert 'END:VCALENDAR' in response.data.decode('utf-8')


@patch('http_server.Client')
def test_calendar_endpoint_authentication_failure(mock_client):
    """Test that authentication failure returns a 500 error."""
    options = create_mock_options()
    app = create_app(options)
    client = app.test_client()

    # Mock TrueNAS client with failed authentication
    mock_truenas_client = MagicMock()
    mock_truenas_client.__enter__ = Mock(return_value=mock_truenas_client)
    mock_truenas_client.__exit__ = Mock(return_value=False)
    mock_truenas_client.call.return_value = False  # Failed authentication
    mock_client.return_value = mock_truenas_client

    response = client.get('/test-calendar')

    assert response.status_code == 500
    assert 'error' in response.json


@patch('http_server.Client')
def test_calendar_endpoint_exception_handling(mock_client):
    """Test that exceptions are handled gracefully."""
    options = create_mock_options()
    app = create_app(options)
    client = app.test_client()

    # Mock TrueNAS client that raises an exception
    mock_client.side_effect = Exception("Connection error")

    response = client.get('/test-calendar')

    assert response.status_code == 500
    assert 'error' in response.json


def test_invalid_calendar_name_validation():
    """Test that invalid calendar names are rejected during options parsing."""
    import os
    from options import Options

    # Save original env vars
    original_calendar_name = os.environ.get('CALENDAR_NAME')
    original_truenas_host = os.environ.get('TRUENAS_HOST')
    original_api_key = os.environ.get('TRUENAS_API_KEY')

    try:
        # Set required env vars
        os.environ['TRUENAS_HOST'] = 'test.local'
        os.environ['TRUENAS_API_KEY'] = 'test-key'

        # Test invalid calendar names
        invalid_names = [
            '../etc/passwd',  # Path traversal
            'calendar/../../secret',  # Path traversal with subdirectories
            'calendar name',  # Spaces
            'calendar@name',  # Special characters
            'calendar.name',  # Dots
            '',  # Empty string
        ]

        for invalid_name in invalid_names:
            os.environ['CALENDAR_NAME'] = invalid_name
            try:
                Options.from_env()
                assert False, f"Should have rejected invalid calendar name: {invalid_name}"
            except Exception as e:
                # Expected to fail
                assert 'Invalid CALENDAR_NAME' in str(e) or 'required' in str(e).lower()

        # Test valid calendar names
        valid_names = ['calendar', 'my-calendar', 'calendar_123', 'TrueNAS-Jobs']
        for valid_name in valid_names:
            os.environ['CALENDAR_NAME'] = valid_name
            options = Options.from_env()
            assert options.calendar_name == valid_name

    finally:
        # Restore original env vars
        if original_calendar_name:
            os.environ['CALENDAR_NAME'] = original_calendar_name
        elif 'CALENDAR_NAME' in os.environ:
            del os.environ['CALENDAR_NAME']

        if original_truenas_host:
            os.environ['TRUENAS_HOST'] = original_truenas_host
        elif 'TRUENAS_HOST' in os.environ:
            del os.environ['TRUENAS_HOST']

        if original_api_key:
            os.environ['TRUENAS_API_KEY'] = original_api_key
        elif 'TRUENAS_API_KEY' in os.environ:
            del os.environ['TRUENAS_API_KEY']
