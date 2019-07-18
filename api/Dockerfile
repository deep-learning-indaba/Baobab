FROM gcr.io/google-appengine/python

RUN virtualenv /env

# Setting these environment variables are the same as running
# source /env/bin/activate.
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

RUN apt-get update -qq
RUN apt-get install -y software-properties-common
RUN apt-get install -y libreoffice 

# Locales
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8
RUN update-locale LANGUAGE=en_US.UTF-8
RUN update-locale LC_ALL=en_US.UTF-8

ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8     

# Add the application source code.
RUN mkdir /code
ADD . /code/
WORKDIR /code

RUN pip install -r requirements.txt
RUN locale -a
EXPOSE 5000
