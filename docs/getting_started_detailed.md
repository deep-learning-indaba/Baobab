# Getting Started (Detailed)

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

8. Read the respective docs for [backend](../api/README.md) and [frontend](../webapp/README.md).
