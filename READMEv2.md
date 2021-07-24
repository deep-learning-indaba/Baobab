<p align="center"><a href="https://www.deeplearningindaba.com" target="_blank" rel="noopener noreferrer"><img src="https://github.com/deep-learning-indaba/Baobab/raw/develop/baobab_logo_small.png" alt="Baobab Logo"></a></p>

<p align="center">
    <a href="http://makeapullrequest.com" target="_blank" rel="noopener noreferrer" alt="PRs Welcome">
        <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" /></a>
    <a href="https://github.com/deep-learning-indaba/Baobab/graphs/contributors" alt="Contributors">
        <img src="https://img.shields.io/github/contributors/deep-learning-indaba/Baobab" /></a>
    <a href="https://github.com/deep-learning-indaba/Baobab/pulse" alt="Activity">
        <img src="https://img.shields.io/github/commit-activity/y/deep-learning-indaba/Baobab" /></a>
    <a href="https://circleci.com/gh/deep-learning-indaba/Baobab/tree/master">
        <img src="https://img.shields.io/circleci/project/github/deep-learning-indaba/Baobab/master" alt="build status"></a>
    <a href="https://join.slack.com/t/baobab-space/shared_invite/enQtOTc1MzUzNjAyODY0LTM2YmJiOTRiNWEyZWRjMjY5ZmNlYTNjY2Y3ODA4MjZjNDljZTFkZWU3YjU5OTk1MTI5MDQwYzI4YzQ0YjFiYzQ" alt="join slack">
        <img src="https://img.shields.io/badge/slack-join_chat-white.svg?logo=slack&style=social" /></a>
    <a href="https://twitter.com/intent/follow?screen_name=DeepIndaba">
        <img src="https://img.shields.io/twitter/follow/DeepIndaba?style=social&logo=twitter" alt="follow on Twitter"></a>
</p>

Baobab is an event management platform primarily aimed for community builders and organisers in the Machine Learning community looking to scale up their efforts. Features include customisable application, review, and registration workflows (in multiple languages), automated email notifications, and all white-labelled for your specific organisation. Currently primarily used by the [Deep Learning Indaba](https://deeplearningindaba.com/).

## Getting Started

First build the docker images.

```console
docker-compose build
```

Then start up the application

```console
docker-compose up
```

The frontend should be available at [localhost:8080](http://localhost:8080) and the backend API at [localhost:5000](http://localhost:5000).

## Project Structure and Tech Stack

- `api/` contains the [Python 3.7](https://www.python.org/) [Flask](https://flask.palletsprojects.com/en/2.0.x/) Web API. See it's [README](./api/README.md) for more details.
- `webapp/` contains the [ReactJS](https://reactjs.org/) frontend. See it's [README](./webapp/README.md) for more details.

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for more details.

Please adhere to this project's [Code of Conduct](CODE_OF_CONDUCT.md).

## License

This project is licensed under the [Apache License 2.0](LICENSE).
