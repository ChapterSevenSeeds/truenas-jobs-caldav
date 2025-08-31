from truenas_api_client import Client
import caldav
from caldav.davclient import get_davclient
from caldav.collection import Calendar
import json

# https://www.truenas.com/docs/api/scale_websocket_api.html#cronjob
# with Client(uri="wss://192.168.254.10/api/current", verify_ssl=False) as c:
#     asdf = c.call("auth.login_with_api_key", "")
#     print(asdf)
#     asdf = c.call("pool.snapshottask.query")
#     print(asdf)
#     asdf = c.call("pool.scrub.query")
#     print(asdf)
#     asdf = c.call("cloudsync.query")
#     print(asdf)
#     asdf = c.call("smart.test.query")
#     print(asdf)
#     asdf = c.call("cronjob.query")
#     print(asdf)

# https://caldav.readthedocs.io/stable/tutorial.html
# https://radicale.org/v3.html
CAL_ID = "TRUENAS_JOBS_CALENDAR"
with get_davclient(url="http://localhost:5232", username="root", password="changeme") as client:
    print("Connecting to the caldav server")
    my_principal = client.principal()

    truenas_calendar: Calendar | None = None
    for cal in my_principal.calendars():
        if cal.id != CAL_ID:
            continue

        truenas_calendar = cal

    if truenas_calendar is None:
        truenas_calendar = my_principal.make_calendar("TrueNAS Jobs", CAL_ID)

    print(truenas_calendar.url)