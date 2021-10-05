FROM gcr.io/google-appengine/python

RUN virtualenv /env -p python3.7

# Setting these environment variables are the same as running
# source /env/bin/activate.
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

RUN apt-get update -qq
RUN apt-get install -y software-properties-common
RUN apt-get install -y libreoffice

RUN mkdir /code
ADD requirements.txt /code/requirements.txt
RUN pip3 install -r /code/requirements.txt

ADD . /code/
WORKDIR /code

RUN locale -a
EXPOSE 5000
