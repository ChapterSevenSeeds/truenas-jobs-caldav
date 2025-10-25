from options import Options
import subprocess
import time

options = Options.from_env()

# Dump the config file
CONFIG_FILE_CONTENT = """[auth]
type = htpasswd
htpasswd_filename = /etc/radicale/users
htpasswd_encryption = autodetect

[rights]
type = from_file
file = /etc/radicale/rights"""

with open("/etc/radicale/config", "w", encoding="utf-8") as config_file:
    config_file.write(CONFIG_FILE_CONTENT)

# Dump the rights file
RIGHTS_FILE_CONTENT = f"""[mainUser]
user: {options.caldav_username}
collection: .*
permissions: RWrw

[anonymous]
user: .*
collection: {options.caldav_username}/{options.calendar_id}(/.*)?
permissions: r"""

with open("/etc/radicale/rights", "w", encoding="utf-8") as rights_file:
    rights_file.write(RIGHTS_FILE_CONTENT)

# Create the users file
subprocess.run(["/usr/sbin/htpasswd", "-cb", "/etc/radicale/users", options.caldav_username, options.caldav_password], check=True)

# Start Radicale
subprocess.Popen(["/app/bin/python", "/app/bin/radicale", "--hosts", "0.0.0.0:5232,[::]:5232"])

# Start the main script
subprocess.Popen(["/app/bin/python", "/truenas-jobs-caldav/main.py"])

# Sleep forever
while True:
    time.sleep(3000)
