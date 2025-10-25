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
RUN /truenas-jobs-caldav/.venv/bin/pip install -r requirements.txt

ENTRYPOINT [ "/truenas-jobs-caldav/.venv/bin/python", "main.py" ]