# TrueNAS Jobs iCalendar HTTP Server

#### A Python script that exposes an HTTP endpoint to retrieve recurring events from a TrueNAS instance as an iCalendar (.ics) file. This makes it easy to see what your TrueNAS server has scheduled!

Can export the following:

- Snapshots
- Scrubs
- Cloud sync tasks
- Cron jobs

# Installation

### Docker

You can spin up a new Docker container to run the HTTP server.

```sh
docker run -d \
-e CALENDAR_NAME=truenas-jobs \
-e HTTP_PORT=8080 \
-e TRUENAS_HOST=my_truenas:9001 \
-e TRUENAS_HOST_VERIFY_SSL=false \
-e TRUENAS_API_KEY=my_api_key \
-v /etc/localtime:/etc/localtime:ro \
-p 8080:8080 \
chaptersevenseeds/truenas-jobs-ical
```

### Docker Compose

If you want to use Docker Compose:

1. Create a `compose.yaml` with your settings (example below).
2. Start the service:

```sh
docker compose up -d
```

3. Fetch your calendar:

```sh
curl http://localhost:8080/truenas-jobs -o calendar.ics
```

Example `compose.yaml`:

```yaml
services:
    truenas-jobs-http:
        restart: unless-stopped
        image: chaptersevenseeds/truenas-jobs-ical
        ports:
            - "8080:8080"
        volumes:
            # Mount the local timezone so that event times are correct
            - /etc/localtime:/etc/localtime:ro
        environment:
            # Required: Calendar name (becomes the URL path)
            - CALENDAR_NAME=truenas-jobs

            # Optional: HTTP server port (default: 8080)
            - HTTP_PORT=8080

            # Required: TrueNAS connection details
            - TRUENAS_HOST=truenas.local:443
            - TRUENAS_HOST_VERIFY_SSL=false
            - TRUENAS_API_KEY=your_api_key_here

            # Optional: Control which job types to include (default: all true)
            - INCLUDE_SNAPSHOTS=true
            - INCLUDE_SCRUBS=true
            - INCLUDE_CLOUDSYNCS=true
            - INCLUDE_CRONJOBS=true

            # Optional: Filter jobs by regex pattern (leave empty for all)
            # - SNAPSHOTS_FILTER=^tank/
            # - SCRUBS_FILTER=^tank$
            # - CLOUDSYNCS_FILTER=backup
            # - CRONJOBS_FILTER=cleanup

            # Optional: Specify custom job summary prefixes
            # - "SNAPSHOTS_SUMMARY_PREFIX=Snapshot: "
            # - "SCRUBS_SUMMARY_PREFIX=Scrub: "
            # - "CLOUDSYNCS_SUMMARY_PREFIX=CloudSync: "
            # - "CRONJOBS_SUMMARY_PREFIX=CRON: "
```

Notes:

- The calendar is generated on-demand for each request.
- The `/etc/localtime` bind mount keeps event times aligned with your local timezone.

## Usage

Once you have the script running, you can access your calendar at:

```
http://localhost:8080/{CALENDAR_NAME}
```

For example, if you set `CALENDAR_NAME=truenas-jobs`, the endpoint would be:

```
http://localhost:8080/truenas-jobs
```

### Example: Using curl

```sh
curl http://localhost:8080/truenas-jobs -o truenas-jobs.ics
```

### Example: Adding to Calendar Applications

You can add this URL directly to most calendar applications (Google Calendar, Apple Calendar, etc.) by subscribing to the URL:

```
http://your-server:8080/truenas-jobs
```

The calendar will automatically update each time it's refreshed by your calendar application.

### Health Check

A health check endpoint is available at `/health`:

```sh
curl http://localhost:8080/health
```

## Environment Variables

These are all the environment variables that the Python script can use.

| Variable                    | Allowed Values                   | Required | Default       | Description                                                                                                                                                                                                 |
| :-------------------------- | :------------------------------- | :------- | :------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CALENDAR_NAME`             | Any URL-safe string.             | Yes      | -             | This becomes the path segment of the HTTP endpoint (e.g., if `CALENDAR_NAME=jobs`, the endpoint will be `/jobs`). Choose a unique, hard-to-guess name for security if exposing to the internet.             |
| `HTTP_PORT`                 | Any valid port number (1-65535). | No       | 8080          | The port on which the HTTP server will listen.                                                                                                                                                              |
| `TRUENAS_HOST`              | Any normal URL host and port.    | Yes      | -             | This is the host of your TrueNAS instance. The script will connect to the websocket endpoint at `wss://{TRUENAS_HOST}/api/current`.                                                                         |
| `TRUENAS_HOST_VERIFY_SSL`   | True or false.                   | No       | true          | Should the script verify SSL of the `wss` endpoint? You'll likely need to set this to false if your instance is serving the default TrueNAS certificate.                                                    |
| `TRUENAS_API_KEY`           | Any string.                      | Yes      | -             | The script will authenticate with your TrueNAS instance using this API key. See [this](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/managingapikeys/) for help with creating a new API key. |
| `INCLUDE_SNAPSHOTS`         | True or false.                   | No       | true          | Include snapshots in the generated iCal events?                                                                                                                                                             |
| `INCLUDE_SCRUBS`            | True or false.                   | No       | true          | Include scrubs in the generated iCal events?                                                                                                                                                                |
| `INCLUDE_CLOUDSYNCS`        | True or false.                   | No       | true          | Include cloudsync tasks in the generated iCal events?                                                                                                                                                       |
| `INCLUDE_CRONJOBS`          | True or false.                   | No       | true          | Include CRON jobs in the generated iCal events?                                                                                                                                                             |
| `SNAPSHOTS_FILTER`          | Python regular expression        | No       |               | Exports only those snapshots whose dataset matches this regular expression. Leave empty to export all.                                                                                                      |
| `SCRUBS_FILTER`             | Python regular expression        | No       |               | Exports only those scrubs whose pool name matches this regular expression. Leave empty to export all.                                                                                                       |
| `CLOUDSYNCS_FILTER`         | Python regular expression        | No       |               | Exports only those cloud sync tasks whose description matches this regular expression. Leave empty to export all.                                                                                           |
| `CRONJOBS_FILTER`           | Python regular expression        | No       |               | Exports only those cronjobs whose description matches this regular expression. Leave empty to export all.                                                                                                   |
| `SNAPSHOTS_SUMMARY_PREFIX`  | Any string.                      | No       | "Snapshot: "  | Specifies the calendar item summary prefix (the default has a single space after the colon).                                                                                                                |
| `SCRUBS_SUMMARY_PREFIX`     | Any string.                      | No       | "Scrub: "     | Specifies the calendar item summary prefix (the default has a single space after the colon).                                                                                                                |
| `CLOUDSYNCS_SUMMARY_PREFIX` | Any string.                      | No       | "CloudSync: " | Specifies the calendar item summary prefix (the default has a single space after the colon).                                                                                                                |
| `CRONJOBS_SUMMARY_PREFIX`   | Any string.                      | No       | "CronJob: "   | Specifies the calendar item summary prefix (the default has a single space after the colon).                                                                                                                |

## TODO

- Fix the TODO in `cron_to_ical.py`.

## Development

Pull requests, issues, questions, and discussions are all more than welcome!
