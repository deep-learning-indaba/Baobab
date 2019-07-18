FROM gcr.io/google-appengine/python

RUN apt-get update -qq
RUN apt-get install -y socat git software-properties-common postgresql-client postgresql-client-common

RUN apt-get update -qq
RUN apt-get install -y python-pip python-psycopg2 libpq-dev python2.7-dev gunicorn libmagic1 libffi-dev

RUN apt-get install -y libreoffice 

RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN pip install -r requirements.txt

EXPOSE 5000
