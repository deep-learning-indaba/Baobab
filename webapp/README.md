# Baobab Webapp

Front-end web application build using [ReactJS](https://react.dev/) and [Tailwind CSS](https://tailwindcss.com/).

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

## Testing
There is no frontend unit-test suite. Frontend changes are verified by running `pnpm run build` and by driving the running app with Playwright and reviewing screenshots (see the `/screenshot` and `verify-feature` skills in `.claude/`). Backend behaviour is covered by the pytest suite in `api/`.

## Connect to local database
```
Host: localhost 
Port: 5432
Database: docker  
User: docker Password: docker 
```
## Project Structure
- src
  - images
  - pages
    - components
  - services


## Adding Code
Add a new folder for each component/page. Name the folder according to the item/feature you are building. Do not include the item type in the name. Example: `Home` **not** `HomePage`.

In each item folder, create a `[item].js` (and a `[item].css` only if Tailwind utilities are not enough). Also create a  `components` folder where you will be break up parts of a page into re-usable components. A page should just be a collection of components, with each component (as far as possible) handling its own logic.

When wanting to call a service, create a folder in the `services` folder with the name of the service and `[service].js` that handles the service calls. 

## Styling
We use [Tailwind CSS](https://tailwindcss.com/) as a CSS framework, with custom design tokens defined in `src/App.css`.

