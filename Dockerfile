FROM python:3.13.3-alpine3.22

RUN apk add git

RUN mkdir /truenas-jobs-caldav
WORKDIR /truenas-jobs-caldav

COPY src/cron_to_ical.py cron_to_ical.py
COPY src/main.py main.py
COPY src/options.py options.py
COPY src/common.py common.py
COPY requirements.txt requirements.txt

RUN python3 -m venv .venv
RUN /truenas-jobs-caldav/.venv/bin/pip install -r requirements.txt

ENTRYPOINT [ "/truenas-jobs-caldav/.venv/bin/python", "main.py" ]