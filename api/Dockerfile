FROM ubuntu:trusty

RUN apt-get update -qq
RUN apt-get install -y --force-yes socat git software-properties-common python-software-properties postgresql-client-9.3 postgresql-client-common

RUN apt-get update -qq
RUN apt-get install -y --force-yes python-pip python-psycopg2 libpq-dev python2.7-dev gunicorn libmagic1 libffi-dev

RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN pip install -r requirements.txt

EXPOSE 5000
