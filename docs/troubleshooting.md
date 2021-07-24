# Troubleshooting

Common errors you may get when running the ```docker-compose build``` or ```docker-compose up``` commands.

| Error                                                                               | Resolution                                                                                                                                                                                                                                          |
| ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Error about "apt-get update -qq" failing                                            | Run `curl -sSL https://get.docker.com/ \| sh` and then rerun the ```docker-compose build``` command.                                                                                                                                                |
| driver failed programming external connectivity on endpoint <IP Address>            | This is a common issue on Windows 10, try stopping all docker containers with ```docker stop $(docker ps -a -q)``` then restart docker on your machine and try again. See [here](https://github.com/docker/for-win/issues/573) for more information |
| Windows Docker-Compose Error  /usr/bin/env: ‘python\r’: No such file or directory | Open run.py in vi or vim (access through git bash) - `vi run.py`, type `:set ff=unix` and save and edit `:wq`.
