# Migration Guide: CalDAV to HTTP Server

This guide helps you migrate from the CalDAV-based sync to the new HTTP server approach.

## What Changed

### Before (v2.x - CalDAV)
- Required a separate CalDAV server (e.g., Radicale)
- Periodically synced TrueNAS jobs to CalDAV
- Calendar accessed via CalDAV protocol
- Used CALENDAR_ID, CALDAV_HOST, CALDAV_USERNAME, CALDAV_PASSWORD

### After (v3.x - HTTP Server)
- No external server needed
- On-demand iCalendar generation via HTTP
- Calendar accessed via simple HTTP GET request
- Uses CALENDAR_NAME and HTTP_PORT

## Migration Steps

### 1. Update Environment Variables

**Remove these variables:**
- `CALDAV_HOST`
- `CALDAV_USERNAME`
- `CALDAV_PASSWORD`
- `SYNC_INTERVAL`
- `FAILURE_BACKOFF_TIME`

**Rename:**
- `CALENDAR_ID` → `CALENDAR_NAME`

**Add (optional):**
- `HTTP_PORT` (default: 8080)

### 2. Update Docker Configuration

**Old configuration:**
```yaml
services:
  truenas-jobs-caldav-sync:
    environment:
      - CALENDAR_ID=my_calendar
      - CALDAV_HOST=radicale:5232
      - CALDAV_USERNAME=username
      - CALDAV_PASSWORD=password
      - TRUENAS_HOST=truenas:9001
      - TRUENAS_API_KEY=my_key
```

**New configuration:**
```yaml
services:
  truenas-jobs-http:
    ports:
      - "8080:8080"
    environment:
      - CALENDAR_NAME=my_calendar
      - HTTP_PORT=8080
      - TRUENAS_HOST=truenas:9001
      - TRUENAS_API_KEY=my_key
```

### 3. Update Calendar Subscriptions

**Old URL format:**
```
http://caldav-server:5232/username/calendar_id
```

**New URL format:**
```
http://server:8080/calendar_name
```

### 4. Remove CalDAV Server

If you were using Radicale or another CalDAV server solely for TrueNAS jobs:
1. Update your calendar subscriptions first
2. Stop the CalDAV server container
3. Remove CalDAV-related volumes and configuration

## Benefits of the New Approach

1. **Simpler Setup**: No need to configure and maintain a separate CalDAV server
2. **Lower Resource Usage**: No periodic syncing or persistent storage needed
3. **On-Demand Updates**: Calendar data is always fresh when accessed
4. **Easier Debugging**: Simple HTTP requests make troubleshooting straightforward

## Security Considerations

- `CALENDAR_NAME` now only accepts alphanumeric characters, hyphens, and underscores
- This prevents path injection attacks
- Choose a hard-to-guess name if exposing to the internet
- Consider using a reverse proxy with authentication for public access

## Testing Your Migration

1. Start the new HTTP server
2. Test the health endpoint:
   ```bash
   curl http://localhost:8080/health
   ```
3. Fetch your calendar:
   ```bash
   curl http://localhost:8080/your-calendar-name -o test.ics
   ```
4. Verify the .ics file contains your TrueNAS jobs
5. Update your calendar applications with the new URL

## Troubleshooting

**Calendar name validation error:**
- Ensure CALENDAR_NAME contains only letters, numbers, hyphens, and underscores
- No spaces, dots, or special characters allowed

**Empty calendar:**
- Check TRUENAS_HOST and TRUENAS_API_KEY are correct
- Verify INCLUDE_* environment variables if using filters

**Connection refused:**
- Ensure HTTP_PORT is correctly exposed in Docker
- Check firewall rules if accessing remotely
