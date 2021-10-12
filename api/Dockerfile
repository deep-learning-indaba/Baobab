FROM gcr.io/google-appengine/python

RUN virtualenv /env -p python3.7

# Setting these environment variables are the same as running
# source /env/bin/activate.
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

RUN apt-get update -qq \
    && apt-get install -y software-properties-common \
    && apt-get install -y libreoffice \
    && python3 -m pip install --upgrade pip

# Add the application source code.
COPY requirements.txt requirements-dev.txt /code/
RUN pip3 install -r /code/requirements.txt -r /code/requirements-dev.txt

ADD . /code/
WORKDIR /code

EXPOSE 5000
