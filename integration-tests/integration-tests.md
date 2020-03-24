# Integration Tests
We use [Cypress](https://www.cypress.io/) for integration tests. 

These tests create a test user and do things like login, register, etc. This happens by programmeably clicking on front-end components and then confirming the expected result happens. These tests, test the full functionality of features and make real calls to backend apis.

## How to Run
### Using docker - headless
Runs part of `docker-compose up`
### Locally - With a UI to click on tests
Follow [instructions](https://docs.cypress.io/guides/getting-started/installing-cypress.html).

## Where to find tests
[Folder](`./cypress/integration) - `./cypress/integration`

## How to add a test
- Add file [test].spec.js
- Copy one of the examples from  `./cypress/integration`   and edit tests.
- Do you need something to happen before all tests (beforeEach) or simple once at the beginning (before) ? - Look at examples.
- Add integration tests - look at other examples in the integration folder or look at the extensive [Cypress Docs](https://docs.cypress.io/guides/getting-started/writing-your-first-test.html#Write-a-real-test). 

## Results of tests
- When cypress has been run, you will see a cmd screen with the results of tests.
- You will also see videos in [here](./cypress/videos) - `./cypress/videos`. These show what happened during each test.
- There are also screenshots for failed tests [here](./cypress/screenshots) - `./cypress/screenshots`.

