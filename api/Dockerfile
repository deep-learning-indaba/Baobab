FROM python:3.11-slim

RUN apt-get update -qq && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

ADD requirements.txt /code/requirements.txt
RUN pip install -r /code/requirements.txt

ADD . /code/
WORKDIR /code

EXPOSE 5000
