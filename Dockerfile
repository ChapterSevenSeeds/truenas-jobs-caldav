FROM python:3.13.7-alpine3.22

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