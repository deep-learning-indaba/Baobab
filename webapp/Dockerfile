# If you change node version here, also change it in ./circleci/config.yml .
FROM node:13

ADD yarn.lock /yarn.lock
ADD package.json /package.json

ENV NODE_PATH=/node_modules
ENV PATH=$PATH:/node_modules/.bin
RUN yarn

WORKDIR /webapp
ADD . /webapp

EXPOSE 3000