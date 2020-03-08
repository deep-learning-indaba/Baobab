Writing your first line of code for Baobab
============================================
###### The web application designed to facilitate the application, review and selection process for large scale machine learning meetings globally

Baobab was initially developed for the annual [Deep Learning Indaba](http://www.deeplearningindaba.com/) which supports the strengthening of machine learning and artificial intelligence within the African community. The Baobab application is now scaling to facilitate the application and selection process for large scale meetings within various machine learning and artificial intelligence communities globally.
Baobab is an open source multi-tenant web application which welcomes the pull requests from all contributors, regardless of skill level or physical location, with the explicit aim of encouraging learning and development. 

What is the technology stack?
-----------------------------
The code base is separated into the front end and back end. These play very different roles, and the decoupled nature thereof means you don’t have to have know much about the front end stack to be able to work on the back end stack (and vice-versa). 
Links to more detailed information on each component in the technology stack can be found in the [README](https://github.com/deep-learning-indaba/Baobab/blob/develop/README.md) on the [Baobab GitHub repository](https://github.com/deep-learning-indaba/Baobab). 
Essentially, the front end handles the user experience, i.e. the display in front of the user of the application. This is where all the information is collected from either the applicant, or the reviewer. The back end handles the underlying data handling and functioning. This is never revealed to the user, but helps ensure a smooth experience for them and ensures their information ends up in the correct places. 
Understanding the difference between the two is the first step in deciding where you would most like to contribute. All issues on GitHub are tagged with either `front-end` or `back-end` so you will easily be able to work out which issues develop either the front end or the back end.

While one doesn’t need to know everything about the tech stack, the technologies need to work in harmony to ensure a functioning application can be built from all corners of the world. An easy way to ensure this, is with [docker](https://docs.docker.com/): a means of packaging the application (and its depending software) in a kind of virtual container. There can then be many instances of an image (i.e. multiple virtual containers) running on many different computers allowing different people with different setups to contribute to the same app development (in this case, Baobab). Docker is explained in more detail next.

Ensuring code runs smoothly
-----------------------------
Running the same code on two PCs can sometimes lead to frustratingly different results - or, error messages. These error messages generally stem from mismatching software versions, or some obscure library that just won’t play nice. Considering the aim of Baobab is to accept pull requests from all contributors (regardless of physical location) mitigating these dependency errors is essential. This is where docker comes in. Docker can be run on various operating systems, including [Windows](https://hub.docker.com/editions/community/docker-ce-desktop-windows), [MacOS](https://hub.docker.com/editions/community/docker-ce-desktop-mac) and Linux ([Ubuntu](https://phoenixnap.com/kb/how-to-install-docker-on-ubuntu-18-04)).

Docker creates a container (packaged up requisite software) for application development. Docker ensures all the dependencies are the same - so that the code can run on separate PCs with the same reproducible analyses and results. Essentially, a virtual computer is bundled into an image, and instances thereof can be run on each PC (the runtime instance of an image is known as a container). Each image is built according to the commands called from the “dockerfile”. All these terms are clearly explained in the [docker glossary](https://docs.docker.com/glossary/).

### Downloading docker
The first step is to [clone](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository) the [Baobab repository](https://github.com/deep-learning-indaba/Baobab). Git and version control will be explained in detail further along in the tutorial.

Docker can now be downloaded by following these links based on your operating system: [Windows](https://hub.docker.com/editions/community/docker-ce-desktop-windows),[MacOS](https://hub.docker.com/editions/community/docker-ce-desktop-mac) and Linux ([Ubuntu](https://phoenixnap.com/kb/how-to-install-docker-on-ubuntu-18-04)).
 
Further installation instructions can be found in Baobab’s [README](https://github.com/deep-learning-indaba/Baobab/blob/develop/README.md).

### Working with docker
Docker is left running in the terminal in the background whenever you want to work on Baobab to ensure there are no dependency / software version errors. The terminal is where you will write your docker [commands](https://afourtech.com/guide-docker-commands-examples/) - such as composing / building the docker image.

### Text editors
If you haven’t work with an [IDE](https://en.wikipedia.org/wiki/Integrated_development_environment) before (integrated development environment), then [PyCharm](https://www.jetbrains.com/pycharm/download/#section=linux) or [VSCode](https://code.visualstudio.com/download) are a good place to start. There are pros to both, but it will most likely come down to personal preference :) 
If you are working on Ubuntu, the PyCharm Community Edition can be downloaded from the software tool. Once your editor is up and running, the next step is to create a project. The project’s path is the same as into the Baobab folder that should be on your computer, having cloned it earlier from GitHub. Working with git and GitHub is explained next.

Version control
----------------
[Git](https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control) is a type of version control, and [GitHub](https://github.com/) is the platform used to assist this process. 
With many streams of code, and many updates from many remote contributors, a clear means of aligning the different versions of the central code base is necessary. This is to ensure seamless integration of all new code into the existing code base. Git also allows for the flexibility to roll back to [earlier versions](https://stackoverflow.com/questions/4114095/how-do-i-revert-a-git-repository-to-a-previous-commit) should the need arise. 
When working with git, there are a few key points that need to be learnt first:
1. [Branches](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging): ach contributor will branch off the main develop branch in order to start submitting proposed changes to the code. The develop branch is the “stable” branch, where all the thoroughly tested code is combined and maintained as the “working” version
2. While writing your code, be sure to [commit](https://chris.beams.io/posts/git-commit/) any changes regularly, so you can also roll back to earlier versions. This is especially useful as your script grows, and you might find things were a little less broken a few additions ago
3. [Pull requests](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request): once the code is ready to possibly be added to the develop branch, you can create a pull request. A pull request is a submission for code review.. The review is done by our highly qualified team of developers who ensure the code does what it is supposed to and meets the conventional standards. There will likely be comments, and change requests - and this is where we learn
4. [Merge](https://www.atlassian.com/git/tutorials/using-branches/git-merge): once the pull request is approved, it will be merged into the main develop branch by one of the pull request reviewers
5. Keeping up to date with the main branch: while you have been working, other contributors are also updating the code. Thus, before starting on a new issue, make sure to [`pull`](https://git-scm.com/docs/git-pull) the develop branch to make sure your remote Baobab repo has the latest version of the code from GitHub

Basic GitHub commands can be found [here](https://confluence.atlassian.com/bitbucketserver/basic-git-commands-776639767.html)
If you aren’t completely comfortable using the terminal commands for GitHub, [“git cola”](https://git-cola.github.io/) is a great GUI to learn to orientate yourself with the various operations, such as writing commit messages (without worrying about poorly placed “” for example) and visualising branching and seeing the differences in a script before committing.

Once you are comfortable with git and the rest of the set up - it's time to choose an issue and get coding. 

Ready to start writing some code?
---------------------------------
### Choosing an issue
Choosing an [issue](https://github.com/deep-learning-indaba/Baobab/issues) depends entirely on your capacity, your abilities and preference. All issues are labeled, and these can be used to guide your decision when choosing an issue. Labels include:
- Front-end / Back-end
- High priority: pull request required in < 2 days
- Low priority: pull request required in < 9 days
- Good first issue: these issues are a good place to start if you are new to Baobab and/or contributing and would like a way to ease yourself into the process
- Bug: an error is occurring in certain circumstances, or something was working, now it isn’t
- Test-feedback / enhancement: these features are working, but following the functional tests some improvements have been suggested

### Understanding where your code touches
 Especially if you are new to contributing, this is an important first step. Understanding where your code touches helps understand how it might influence the rest of the code base, and help you plan your own code.
 
### The importance of writing tests
Tests are the first line of defence in ensuring one's code is working and doing what it is supposed to. Writing tests as you go along will save a lot of time debugging down the line, when the code base is so large is difficult to pinpoint the source of the error. 
There are various kinds of tests one should always keep in mind writing code:
1. [Regression tests](https://smartbear.com/learn/automated-testing/what-is-regression-testing/): these ensure that any changes to the existing software don’t cause any breakages
2. [Integration tests](https://www.guru99.com/integration-testing.html): these tests are run when different components are tested together to see if they are all still logically integrated
3. [Unit tests](https://smartbear.com/learn/automated-testing/what-is-unit-testing/): these are the tests written to test each function (the smallest component of the script) and is the kind of testing you will become most familiar with when contributing to Baobab. These should be written before each function, and then tested thoroughly once the function is complete
 
### Migrations and databases (for back-end developers)
Databases are used to organise and store information for easy information access and retrieval.
[PostgreSQL](https://www.postgresqltutorial.com/what-is-postgresql/) is an fully object-relational database management system (i.e. it is the database). SQL [(Structured Query Language)](http://www.sqlcourse.com/intro.html) is the language used for communication  with the database.
[ORM](https://www.fullstackpython.com/object-relational-mappers-orms.html) (object-relational mapper) allows the programmer to communicate with the database in a Python, instead of the database query language (or SQL) which can get quite complicated. 

#### What are migrations?
A migration is basically a database change in code (Python code). When run it makes the necessary SQL queries to update your database from a specific state (the previous migration) to the new state. The code base is stored on GitHub, and all information collected by the Baobab application is stored in databases. The same way we need to ensure our code is up to date with the develop branch of Baobab, we also need to ensure the database schemas stay up to date. The database schema refers to the tables, and the structure thereof (less so the actual data in the database). This is achieved through migrations.
#### When should one run migrations?
These are only necessary for back-end development. A migration should be run as soon as you clone a new project (i.e. when you are first setup). Migrations should be repeated whenever a database is generated, or, alternatively ater pulling code from a branch where someone has made a database change.

### Writing code
By this point, your PC should pretty much be up and running smoothly (and you feeling to confident) to allow you to actually make some changes. Remember to commit your own changes, so they can be tracked on your branch (which branches off develop), and then when you are ready you can create your pull request.
Remember to include "Resolves #<issue number>" in your PR, so that GitHub automatically closes the issue. This helps keep the backlog clean and prevents more than one person working on the same issue!

If you have any questions, please don't hesitate to leave them in the comment section on GitHub and they will be answered as soon as possible. 


