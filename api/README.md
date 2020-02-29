# Baobab API

Built using Flask and SQLAlchemy

## Prerequisites
### Running with Docker.

The development environment uses [Docker](http://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/). This makes it super easy to get up and running with a configuration that would closely mirror production. 

### Running locally
- TBC

## Installation

With Docker/Compose installed, use the following steps to launch for the first time:

* `docker-compose up` to start the web app. This will download and provision two containers: one running PostgreSQL and one running the Flask app. This will take a while, but once it completes subsequent launches will be much faster.
* When `docker-compose up` completes, the app should be accessible at [http://127.0.0.1:5000](http://127.0.0.1:5000).


## Environment Variables


There are just a couple of configurations managed as environment variables. In the development environment, these are injected by Docker Compose and managed in the `docker-compose.yml` file.

* `DATABASE_URL` - This is the connection URL for the PostgreSQL database. It is not used in the **development environment**.
* `DEBUG` - This toggle debug mode for the app to True/False.
* `SECRET_KEY` - This is a secret string that you make up. It is used to encrypt and verify the authentication token on routes that require authentication.


## Project Organization


* Application-wide settings are stored in `config.py` at the root of the repository. These items are accessible on the `config` dictionary property of the `app` object. Example: `debug = app.config['DEBUG']`
* The directory `/app` contains the API application
* URL mapping is managed in `/app/routes.py`
* Functionality is organized in packages. Example: `/app/users` or `/app/utils`.
* Tests are contained in each package. Example: `app/users/tests.py`


## Running Tests


Tests are run with [nose](https://nose.readthedocs.org/en/latest/) from inside the `docker-compose` web container.

### Run All

```
docker-compose run web nosetests
```

### Run Specific Tests
As the project has grown, so has the number of tests and the amount of time needed to run them all. Luckily, you can progressively get more and more specific about which tests you can run making your feedback loop shorter and thus speeding up the development process.

#### Run all tests in a file
We will use `invitedGuest` as the example.
```
docker-compose run web bash -c 'cd api; nosetests -v app.invitedGuest.tests'
```
On Windows, you may need to break the command above up to get into the container, open the correct directory, and then finally to run the tests
```
docker-compose run web bash
cd api
nosetests -v app.invitedGuest.tests
```

#### Run all tests in a class

```
nosetests -v app.invitedGuest.tests:InvitedGuestTest
```

#### Run a specific test
```
nosetests -v app.invitedGuest.tests:InvitedGuestTest.test_create_invitedGuest
```




## Database Migrations

When a class inherits from the SQL Alchemy `db.Model` class, it represents the code format of an actual table in the database. This means that whenever fields are added, edited, or removed from these classes, the corresponding change needs to be made in the database. Luckily, this process can be automated in the form of a _migration_ so you usually only ever have to make the changes in code.

Migrations for the provided models are part of the seed project. To generate a new migration use `Flask-Migrate`:

```
docker-compose run web python ./api/run.py db migrate --directory api/migrations
```

Assuming no errors occurred (generally this will happen if there's a syntax error in your code), this should generate the script. If you look in your project directory, you will see a new file has been added to `./app/migrations/versions`. You'll also see all the other files that have been generated previously.

Open the file and verify that in the `upgrade()` method the changes you made have been added and in the `downgrade()` method, the changes have been removed. The `upgrade()` is for when we deploy and the `downgrade()` is for if we decide to rollback a change on production.

Once you're happy with the script, run the following command.

```
docker-compose run web python ./api/run.py db upgrade --directory api/migrations
```

This should now actually run the script that was generated and apply the changes to the local instance of the database.

### Merging migrations

If you run into the following error while attempting a migration, it means that a migration was created on separate concurrent git branches from the same base. 

`Multiple head revisions are present for given argument 'head'; please specify a specific target revision, '@head' to narrow to a specific head, or 'heads' for all heads`

Running the below command should create a new migration that will merge them (note it will be empty although you will notice multiple entries in the `down_revision` variable). See this [link](https://blog.jerrycodes.com/multiple-heads-in-alembic-migrations/) to understand this error and solution in more detail.
```
docker-compose run web python ./api/run.py db merge --directory api/migrations heads
```

## API Routes


This API uses token-based authentication. A token is obtained by registering a new user (`/api/v1/user`) or authenticating an existing user (`/api/v1/authenticate`). Once the client has the token, it must be included in the `Authorization` header of all requests.


### Register a new user

**POST:**
```
/api/v1/user
```

**Body:**
```json
{
    "email": "something@email.com",
    "password": "123456"
}
```

**Response:**
```json
{
    "id": 2,
    "token": "eyJhbGciOiJIUzI1NiIsImV4cCI6MTQxMDk2ODA5NCwiaWF0IjoxNDA5NzU4NDk0fQ.eyJpc19hZG1pbiI6ZmFsc2UsImlkIjoyLCJlbWFpbCI6InRlc3QyQHRlc3QuY29tIn0.goBHisCajafl4a93jfal0sD5pdjeYd5se_a9sEkHs"
}
```

**Status Codes:**
* `201` if successful
* `400` if incorrect data provided
* `409` if email is in use


### Get the authenticated user

**GET:**
```
/api/v1/user
```

**Response:**
```json
{
    "id": 2,
    "email": "test2@test.com",
}
```

**Status Codes:**
* `200` if successful
* `401` if not authenticated


### Authenticate a user

**POST:**
```
/api/v1/authenticate
```

**Body:**
```json
{
    "email": "something@email.com",
    "password": "123456"
}
```

**Response:**
```json
{
    "id": 2,
    "token": "eyJhbGciOiJIUzI1NiIsImV4cCI6MTQxMDk2ODA5NCwiaWF0IjoxNDA5NzU4NDk0fQ.eyJpc19hZG1pbiI6ZmFsc2UsImlkIjoyLCJlbWFpbCI6InRlc3QyQHRlc3QuY29tIn0.goBHisCajafl4a93jfal0sD5pdjeYd5se_a9sEkHs"
}
```

**Status Codes:**
* `200` if successful
* `401` if invalid credentials
