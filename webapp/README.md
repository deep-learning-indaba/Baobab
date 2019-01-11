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

## Project Structure
- src
  - components
  - containers
  - images
  - pages


## Adding Code
Add a new folder for each component/container/page. Make the name of the folder, the name of what the item you are building. Do not include the item type in the name. Example: `Home` **not** `HomePage`.

In each item folder, create a `[item].js`, `[item].css` and `__tests__/[item].test.js`.

## Adding Tests
We are using Jest + Enzyme as a testing framework. Read this [article](https://hackernoon.com/testing-react-components-with-jest-and-enzyme-41d592c174f), which explains how to use jest and enzyme. Note we are not doing snapshot testing - simply testing rendering, props and events.

Example
```javascript
import React from 'react';
import {shallow} from 'enzyme';
import Home from '../Home.js';

test('Check if Home component renders.', () => {
  // Render Home main component.
  const wrapper = shallow(<Home />);
  expect(wrapper.length).toEqual(1);
});
```
## Styling
We use react-bootstrap as a component library, details and components can be found [here](https://react-bootstrap.github.io/).

