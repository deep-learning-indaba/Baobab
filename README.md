<p align="center"><a href="https://www.deeplearningindaba.com" target="_blank" rel="noopener noreferrer"><img src="https://github.com/deep-learning-indaba/Baobab/raw/develop/baobab_logo_small.png" alt="Baobab Logo"></a></p>

<p align="center">
    <a href="http://makeapullrequest.com" target="_blank" rel="noopener noreferrer" alt="PRs Welcome">
        <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" /></a>
    <a href="https://github.com/deep-learning-indaba/Baobab/issues/" alt="open issues">
        <img src="https://img.shields.io/github/issues/deep-learning-indaba/Baobab" /></a>
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

Baobab is an event management platform primarily aimed at community builders and organisers in the Machine Learning community looking to scale up their efforts. Features include customisable application, review, and registration workflows (in multiple languages), automated email notifications, and white-labelling for your specific organisation. Currently primarily used by the [Deep Learning Indaba](https://deeplearningindaba.com/).

## Getting Started

First build the docker images,

```console
docker-compose build
```

run the database migrations,

```console
docker-compose run web python ./api/run.py db upgrade --directory api/migrations
```

and then start up the application with

```console
docker-compose up
```

The frontend should now be available at [http://localhost:8080](http://localhost:8080) and the backend API at [http://localhost:5000](http://localhost:5000).

If you had any problems, have a look at our more [detailed getting started](./docs/getting_started_detailed.md) guide and/or our [troubleshooting](./docs/troubleshooting.md) guide. Answers to other questions may possibly be found in our [FAQs](./docs/faq.md).

Now that you've setup, dig deeper into the Python 3.7 Flask API backend in `api/` or the ReactJS frontend in `webapp/` which each have their own READMEs [here](./api/README.md) and [here](./webapp/README.md) respectively.

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for more details and adhere to this project's [Code of Conduct](CODE_OF_CONDUCT.md).

In summary, tasks are managed via the [Issues](https://github.com/deep-learning-indaba/Baobab/issues) tab and labelled according to whether they involve the _backend_ or _frontent_ primarily. If you want to work on a particular issue, please assign yourself to it. Each issue should include a _definition of done_ checklist that should be met before submitting a pull request to merge into the `develop` branch. Although if you're stuck or unsure of anything, submit the pull request anyway and we can give you feedback and iterate until it's ready.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
