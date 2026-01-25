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
chaptersevenseeds/truenas-jobs-caldav-sync
```

### Docker Compose

If you want to use Docker Compose:

```yaml
# compose.yaml

services:
    truenas-jobs-http:
        restart: unless-stopped
        image: chaptersevenseeds/truenas-jobs-caldav-sync
        volumes:
            # We need this so that the times for all iCal events are correct (assuming the machine running this script will have the same timezone as your TrueNAS machine).
            - /etc/localtime:/etc/localtime:ro
        ports:
            - 8080:8080
        environment:
            - CALENDAR_NAME=truenas-jobs
            - HTTP_PORT=8080
            - TRUENAS_HOST=my_truenas:9001
            - TRUENAS_HOST_VERIFY_SSL=false
            - TRUENAS_API_KEY=my_api_key
```

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

| Variable                  | Allowed Values                   | Required | Default | Description                                                                                                                                                                                                 |
| :------------------------ | :------------------------------- | :------- | :------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CALENDAR_NAME`           | Any URL-safe string.             | Yes      | -       | This becomes the path segment of the HTTP endpoint (e.g., if `CALENDAR_NAME=jobs`, the endpoint will be `/jobs`). Choose a unique, hard-to-guess name for security if exposing to the internet.             |
| `HTTP_PORT`               | Any valid port number (1-65535). | No       | 8080    | The port on which the HTTP server will listen.                                                                                                                                                              |
| `TRUENAS_HOST`            | Any normal URL host and port.    | Yes      | -       | This is the host of your TrueNAS instance. The script will connect to the websocket endpoint at `wss://{TRUENAS_HOST}/api/current`.                                                                         |
| `TRUENAS_HOST_VERIFY_SSL` | True or false.                   | No       | true    | Should the script verify SSL of the `wss` endpoint? You'll likely need to set this to false if your instance is serving the default TrueNAS certificate.                                                    |
| `TRUENAS_API_KEY`         | Any string.                      | Yes      | -       | The script will authenticate with your TrueNAS instance using this API key. See [this](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/managingapikeys/) for help with creating a new API key. |
| `INCLUDE_SNAPSHOTS`       | True or false.                   | No       | true    | Include snapshots in the generated iCal events?                                                                                                                                                             |
| `INCLUDE_SCRUBS`          | True or false.                   | No       | true    | Include scrubs in the generated iCal events?                                                                                                                                                                |
| `INCLUDE_CLOUDSYNCS`      | True or false.                   | No       | true    | Include cloudsync tasks in the generated iCal events?                                                                                                                                                       |
| `INCLUDE_CRONJOBS`        | True or false.                   | No       | true    | Include CRON jobs in the generated iCal events?                                                                                                                                                             |
| `SNAPSHOTS_FILTER`        | Python regular expression        | No       |         | Exports only those snapshots whose dataset matches this regular expression. Leave empty to export all.                                                                                                      |
| `SCRUBS_FILTER`           | Python regular expression        | No       |         | Exports only those scrubs whose pool name matches this regular expression. Leave empty to export all.                                                                                                       |
| `CLOUDSYNCS_FILTER`       | Python regular expression        | No       |         | Exports only those cloud sync tasks whose description matches this regular expression. Leave empty to export all.                                                                                           |
| `CRONJOBS_FILTER`         | Python regular expression        | No       |         | Exports only those cronjobs whose description matches this regular expression. Leave empty to export all.                                                                                                   |

## TODO

- Fix the TODO in `cron_to_ical.py`.

## Development

Pull requests, issues, questions, and discussions are all more than welcome!
