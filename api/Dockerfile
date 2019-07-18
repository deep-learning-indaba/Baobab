FROM gcr.io/google-appengine/python

RUN virtualenv /env

# Setting these environment variables are the same as running
# source /env/bin/activate.
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

RUN apt-get update -qq
RUN apt-get install -y software-properties-common
RUN apt-get install -y libreoffice 

# Copy the application's requirements.txt and run pip to install all
# dependencies into the virtualenv.
ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Add the application source code.
ADD . /app

RUN pip install -r requirements.txt
RUN locale -a
EXPOSE 5000
