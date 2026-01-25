# TrueNAS Jobs HTTP Server - Docker Compose Example

This example shows how to run the TrueNAS Jobs HTTP server as a standalone service.

## Quick Start

1. Edit `compose.yaml` and set your environment variables:
   - `CALENDAR_NAME`: Choose a unique name for your calendar (becomes the URL path)
   - `TRUENAS_HOST`: Your TrueNAS server hostname and port
   - `TRUENAS_API_KEY`: Your TrueNAS API key

2. Start the service:
   ```bash
   docker compose up -d
   ```

3. Access your calendar:
   ```bash
   curl http://localhost:8080/truenas-jobs -o calendar.ics
   ```

## Usage

Once running, you can:

- **Access the calendar**: `http://localhost:8080/truenas-jobs` (replace with your `CALENDAR_NAME`)
- **Health check**: `http://localhost:8080/health`
- **Subscribe in calendar apps**: Use the full URL in Google Calendar, Apple Calendar, etc.

## Environment Variables

See the main README.md for a complete list of configuration options.

## Notes

- The calendar is generated on-demand for each request
- Events are filtered based on your configuration
- Times are synchronized with your local timezone via the `/etc/localtime` mount
