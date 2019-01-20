# Baobab

Deep Learning Indaba applications and selection web application.

# Structure

- `api/` contains the flask-based web api
- `webapp/` contains the react front-end

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Tasks

Tasks are being managed in the Issues and Projects tabs. If you want to work on a particular issue, please assign yourself to it. Each issue should include a "definition of done" checklist that should be met before submitting a pull request to merge into the develop branch. 

## Technology Stack
**Backend**
* **Language**: [Python](https://www.python.org/)
* **Database**: [PostgreSQL](https://www.postgresql.org/)
* **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/)
* **REST API**: [Flask](http://flask.pocoo.org/)

**Frontend**
* **Language**: [Javascript](https://developer.mozilla.org/bm/docs/Web/JavaScript)
* **Components**: [ReactJS](https://reactjs.org/)
* **CSS**: [Bootstrap 4](https://getbootstrap.com/)

You don't need to be familar with all of these technologies to work on the project. We've tried to make the application decoupled, especially the front-end and back-end. If you want to work on a front-end task, you need to know a little Javascript, ReactJS and Bootstrap, but don't need to know anything about Flask/SQLAlchemy etc!  

## Running with Docker
We are using Docker which means you don't need to install any of the dependencies on your local machine (except for docker itself). If you are already familiar with Docker and the technologies listed above, you can clone the repository to you local machine and bring up the database, back-end and front-end together with:

```docker-compose build```

```docker-compose up```

The front-end will then be available at localhost:8080 and the backend API at localhost:5000

If you are not familiar with this style of development, here is a more detailed description:

## Getting Started (Detailed)
1. Make sure you have the following installed on your machine:
* Git: [Windows](https://git-scm.com/download/win), [Mac](https://git-scm.com/download/mac). (Linux users should install using their system's package manager)
* Docker: [Windows](https://docs.docker.com/docker-for-windows/install/), [Mac](https://docs.docker.com/docker-for-mac/install/), [Linux](https://docs.docker.com/install/linux/docker-ce/ubuntu/) (ensure you have the latest version!)

2. Ensure that docker is running on your machine by running ```docker run hello-world``` 

3. Clone (copy to your local machine) the repository using the command:
```git clone https://github.com/deep-learning-indaba/Baobab.git```

4. Navigate to the Baobab folder (```cd Baobab```)

5. Build the containers using ```docker-compose build``` -  this will build the front-end, back-end and database together.
It will take a fair bit of time the first time you do it, subsequently it will be much faster. If you get any errors, check the **troubleshooting** section below. If you get any other errors at this step, please get in touch!  

6. Launch the containers using ```docker-compose up``` - you should see messages like "Starting baobab_webapp_1 ... done". You can then navigate to the application in your browser at ```http://localhost:8080```. The back-end API can be found at ```http://localhost:5000``` (note, you won't see anything if you navigate to localhost:5000 in your browser) 

7. The first time you run the app, you may need to run the **migrations** to ensure that all the tables are created in the database. While the app is running (after following the previous step), run the following in **another terminal/command prompt**: ```docker-compose run web python ./api/run.py db upgrade --directory api/migrations```

## Troubleshooting
Common errors you may get when running the ```docker-compose build``` or ```docker-compose up``` commands.

|Error|Resolution|
|-----|----------|
|Error about "apt-get update -qq" failing | Run `curl -sSL https://get.docker.com/ \| sh` and then rerun the ```docker-compose build``` command.|
|driver failed programming external connectivity on endpoint <IP Address> | This is a common issue on Windows 10, try stopping all docker containers with ```docker stop $(docker ps -a -q)``` then restart docker on your machine and try again. See [here](https://github.com/docker/for-win/issues/573) for more information|


## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

* TBC.
