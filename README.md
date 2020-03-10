# Baobab


![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
[![Slack Status](https://img.shields.io/badge/slack-join_chat-white.svg?logo=slack&style=social)](https://join.slack.com/t/baobab-space/shared_invite/enQtOTc1MzUzNjAyODY0LTM2YmJiOTRiNWEyZWRjMjY5ZmNlYTNjY2Y3ODA4MjZjNDljZTFkZWU3YjU5OTk1MTI5MDQwYzI4YzQ0YjFiYzQ)
![Slack Status](https://img.shields.io/twitter/follow/DeepIndaba?label=Follow&style=social)


Baobab is an open source multi-tenant web application designed to facilitate the application and selection process for large scale meetings within the machine learning and artificial intelligence communities globally.

## Application Lifecycle

The process starts with the release of an application form for potential applicants to complete online. Once all the applications are in, reviewers assess each one by completing a form of their own which is used to record the decisions on each applicant.

Following the selection process, applicants are informed of the decision and relevant information regarding the event and reference letters (for visas etc.) are dispatched.

Lastly, successful applicants can then register to confirm they will attend as well as check-in at the event itself.

# Structure

- `api/` contains the flask-based web api
- `webapp/` contains the react front-end

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Tasks

Tasks are managed via the [Issues](https://github.com/deep-learning-indaba/Baobab/issues) tab. If you want to work on a particular issue, please assign yourself to it. Each issue should include a _definition of done_ checklist that should be met before submitting a pull request to merge into the develop branch. Although if you're stuck or unsure of anything, submit the pull request anyway and we can give you feedback and iterate until it's ready.

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

**Continuous Integration**
We are using [CircleCI](https://circleci.com/gh/deep-learning-indaba/Baobab) to build, test and deploy the project. 

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

| Error                                                                               | Resolution                                                                                                                                                                                                                                          |
| ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Error about "apt-get update -qq" failing                                            | Run `curl -sSL https://get.docker.com/ \| sh` and then rerun the ```docker-compose build``` command.                                                                                                                                                |
| driver failed programming external connectivity on endpoint <IP Address>            | This is a common issue on Windows 10, try stopping all docker containers with ```docker stop $(docker ps -a -q)``` then restart docker on your machine and try again. See [here](https://github.com/docker/for-win/issues/573) for more information |
| Windows Docker-Compose Error  /usr/bin/env: ‘python\r’: No such file or directory | Open run.py in vi or vim (access through git bash) - `vi run.py`, type `:set ff=unix` and save and edit `:wq`.                                                                                                                                      |
## Frequently Asked Questions

* **I have never worked on a large scale project like this before. Should I jump right in, or how much code should I look at first?**

    This depends on you. The most important thing to remember is that you don't have to worry about breaking anything. All code is reviewed and tested before being deployed so jumping right in or taking a slower and more measured approach are both fine. The issue descriptions should also contain enough information to get you started and if not, a comment asking for clarification is more than welcome.

* **What are the expected time frames regarding the high and low priority?**

    High priority: pull request within two days.

    Low priority: pull request after seven to nine days.

* **I can’t help right now, but I should free up in a month or two - can I still help?**

    Baobab will log a continuous stream of new issues, bugs that creep in, or new features needed. 

* **My country doesn’t allow for docker to installed**

    [Windscribe](https://windscribe.com/) is a free VPN that doesn’t require a credit card for set up and can potentially help with the install. Tor browsers are also a potential avenue to try out. If you find a workaround that works, please let us know!

* **How much disk space is required to run the project?**

    The docker images, containers, and volumes use up approximately 4.7GB of disk space.

* **I have a question about the issue, where should I ask?**

    All questions relating to a specific issue, should be left on the GitHub on the issue itself (or the Pull Request if you've opened one).

    Please be as descriptive as possible, and include any error messages you might be experiencing.

    If you have any time, please peruse the other issues and see if there are other questions you can answer. We are here to learn from each other!



## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
