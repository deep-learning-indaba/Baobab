FROM node:8 as build-deps
WORKDIR /webapp
COPY package.json yarn.lock ./
RUN yarn
COPY . ./
RUN yarn build

FROM nginx:1.12-alpine
COPY --from=build-deps /webapp/nginx.conf /etc/nginx/nginx.conf
COPY --from=build-deps /webapp/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
