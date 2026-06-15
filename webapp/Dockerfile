FROM node:22-alpine

RUN npm install -g pnpm@10

WORKDIR /webapp
COPY .npmrc pnpm-lock.yaml package.json ./
RUN pnpm install --frozen-lockfile

COPY . .

EXPOSE 3000
CMD ["pnpm", "start"]
