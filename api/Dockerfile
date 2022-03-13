FROM gcr.io/google-appengine/python

RUN virtualenv /env -p python3.7

# Setting these environment variables are the same as running
# source /env/bin/activate.
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

RUN apt-get update -qq \
    && apt-get install -y software-properties-common \
    && apt-get install -y libreoffice

# Upgrade pip
RUN python -m pip install --upgrade pip

# Add the application source code.
ADD requirements.txt /code/requirements.txt
RUN pip3 install -r /code/requirements.txt

ADD . /code/
WORKDIR /code

EXPOSE 5000
