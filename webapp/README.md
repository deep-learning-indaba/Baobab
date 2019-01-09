# Baobab Webapp

Webapp build using React.

### Prerequisites
#### Runnning through Docker.
- Docker 

#### Running locally.
- Node version 7 or higher.
- Yarn.


## How to Run

#### Runnning through Docker.
- Install [Docker](https://docs.docker.com/install/)
- Navigate to webapp folder.
- Build Website Container.
```
docker build . -t website
```
- Run Website Container on port 8080.
```
docker run -p 8080:80 website
```

### Running locally.
- Install [Node](https://nodejs.org/en/download/) and [Yarn](https://yarnpkg.com/lang/en/docs/install/#debian-stable).
- Navigate to webapp folder.
- Install dependencies.
```
yarn
```
- Run website.
```
yarn start
```

## Running the tests

### Running Locally
- Run Test
```
yarn test
```