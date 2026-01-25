FROM python:3.13.3-alpine3.22

RUN apk add git

RUN mkdir /truenas-jobs-ical
WORKDIR /truenas-jobs-ical

COPY src/cron_to_ical.py cron_to_ical.py
COPY src/main.py main.py
COPY src/options.py options.py
COPY src/common.py common.py
COPY src/job_fetcher.py job_fetcher.py
COPY src/http_server.py http_server.py
COPY requirements.txt requirements.txt

RUN python3 -m venv .venv
RUN /truenas-jobs-ical/.venv/bin/pip install -r requirements.txt

HEALTHCHECK --interval=1m --timeout=3s --retries=3 --start-period=10s \
    CMD ["/truenas-jobs-ical/.venv/bin/python", "-c", "import os, urllib.request; port=os.getenv('HTTP_PORT','8080'); urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=2).read()"]

ENTRYPOINT [ "/truenas-jobs-ical/.venv/bin/python", "main.py" ]