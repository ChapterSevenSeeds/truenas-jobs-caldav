# Base image, contains just the main script
FROM python:3.14.0-alpine3.22 AS base

RUN apk add git

RUN mkdir /truenas-jobs-caldav
WORKDIR /truenas-jobs-caldav

COPY cron_to_ical.py cron_to_ical.py
COPY main.py main.py
COPY options.py options.py
COPY requirements.txt requirements.txt

RUN python3 -m venv .venv
RUN pip install -r requirements.txt

CMD [ "python3", "main.py" ]

# AIO image, contains management script and Radicale
FROM ghcr.io/kozea/radicale:3.5.7 AS aio

COPY --from=base /truenas-jobs-caldav /truenas-jobs-caldav
WORKDIR /truenas-jobs-caldav
COPY aio_management.py aio_management.py

CMD [ "python3", "aio_management.py" ]