Glossary of useful concepts
============================
###### Narrowing the search space when you don’t even know what you don’t know

## Backend technology stack
This is divided into two sections. The technology stack is described first, as an introduction to the backend technologies used in Baobab. All words in **bold** are also defined within this document.

### Python
[Python](https://www.python.org/doc/essays/blurb/) is an interpreted object-orientated, high level programming language with dynamic semantics.
Let’s break that up:

**1. Interpreted versus compiled languages:**

Languages can have implementations of both

- Compiled:
written code is converted directly into machine code that the processor executes
More control over hardware (memory, CPU usage). Examples are C, C++, Go
- Interpreted: 
these languages will run through the programme line by line and execute each.
Examples include JavaScript, Python

**2. Object-orientated programming**
- This centres around the creation of objects that are characterised by attributes and behaviour. 
- **Classes** are used in OOP in the creation of objects. High-level versus low-level languages
- This refers to the level of abstraction. Each level is a step away from the base machine 
    - Abstraction: the degree to which the characteristics of an object are hidden in order to reduce complexity and increase efficiency. The remaining object is a representation of the original with unwanted detail omitted
    - Higher level languages have greater levels of abstraction 

**3. Dynamic semantics**
- This defines how and when the various constructs of a programming language should produce a programme behaviour
- Constructs refer to instances of values contained into so-called constructs which exist at runtime. This helps the flow of execution of the programme.

## The database and ORM
Databases are used to organise and store information for easy information access and retrieval (essentially create, read, update and delete information). There are varying kinds of databases, viz. [spatial](https://www.tutorialspoint.com/Spatial-Databases), [non-relational](https://docs.microsoft.com/en-us/azure/architecture/data-guide/big-data/non-relational-data), [XML](https://www.tutorialspoint.com/xml/xml_databases.htm) and [graph](https://towardsdatascience.com/graph-databases-whats-the-big-deal-ec310b1bc0ed) databases.

The type of database we are interested in is a **relational database**.
[PostgreSQL](https://www.postgresqltutorial.com/what-is-postgresql/) is an fully object-relational database management system and is the chosen database for Baobab. SQL [(Structured Query Language)](http://www.sqlcourse.com/intro.html) is the language generally used for communication  with the database. However, SQL can be quite complicated, and tricky to work with if you are used to working in Python. Luckily, [ORM](https://www.fullstackpython.com/object-relational-mappers-orms.html) (object-relational mapper) exists for this very reason. ORM allows the programmer to communicate with the database in Python, instead of the database query language (or SQL) which can get quite complicated. [SQLAlchemy](https://towardsdatascience.com/sqlalchemy-python-tutorial-79a577141a91) is a library that allows us to communicate with the relational database more fluent in Python syntax by translating python classes to tables in the database and converts function calls to SQL statements. 

## Flask 
The REST **API** used is Flask. Flask is a Python micro [web-based framework](https://www.fullstackpython.com/web-frameworks.html) that is flexible and simple to implement when creating web-based applications such as Baobab. The main thing to remember about web-frameworks is that they are essentially code libraries that provide common methods / operations for building reliable, scalable, and maintainable web applications
The simplicity of Flask, compared to another framework such as [Django](https://www.djangoproject.com/), is particularly advantageous due to Baobab supporting remote contributors who may not have a lot of experience with web-application development. 

Glossary
========
## APIs (application programming interfaces)
APIs allow for communication between two systems. The API provides the documentation and specifications of this interaction (for example: how information can be transferred ). APIs are categorised as [SOAP](https://en.wikipedia.org/wiki/SOAP) or [**REST**](https://restfulapi.net/). [Baobab’s](https://github.com/deep-learning-indaba/Baobab/blob/develop/README.md) API is categorised as RESTful; and as such only REST will be further described.
REST uses [**URIs**](https://danielmiessler.com/study/difference-between-uri-url/) (universal resource identifiers) to send and receive information. Under the umbrella of URI’s, we have [**URLs**](https://danielmiessler.com/study/difference-between-uri-url) (universal resource locators) which provide resource accessing information, viz. locations and methods. Specifically, the methods are known as  [**HTTP**](https://www.restapitutorial.com/lessons/httpmethods.html) verbs such as `GET`(read), `POST`(create), `PUT`(update/replace), `PATCH`(update/modify) `DELETE`(delete).
REST also outputs the data in a form that is easy to parse within the language of the application: such as [CSV files](https://en.wikipedia.org/wiki/Comma-separated_values),  [JSON](https://en.wikipedia.org/wiki/JSON) and [XML](https://en.wikipedia.org/wiki/XML). 

## Classes
- What is a class?
    - Classes are fundamental in object oriented programming and centre around creating reusable patterns of code
    - Classes are blueprints for an object: the blueprint defines a set of attributes that will characterise any object instantiated from a class
    - An instance of the class is a realised version of the class. In other words, when the class object is run in your _“run.py”_ file, with your respective input parameters.
- When should write a function over a class:
    - Function: single, repetitive task e.g. calculating the sum of an array (not all languages have these built-in)
    - Class: this is the creation of an idea which requires a collection of properties (attributes) pertaining to the idea. These can include a collection of function(s). Functions are referred to as methods. The class will be instantiated repeatedly - without having to build the object from scratch each time.
- Classes take some getting used to, and there are many aspects like inheritance and  This [tutorial series on classes](https://www.digitalocean.com/community/tutorials/how-to-construct-classes-and-define-objects-in-python-3) is a good place to start.

## Clients and servers
**1. Clients**
- Computer hardware and/or software that accesses a service made available by a server, which is often on another computer. Clients access and modify resources (content)

**2. Servers**
- Manages access to a centralised resource / service in a network

## Decorators (in Python)
These are used in programming as wrappers around a function or object in order to modify it’s behaviour. Decorators are placed above a function with following characteristic syntax:
`@nameofdecorator`
Each decorator will modify an aspect of the original function or a class’s behaviour in a specific way without permanently modifying it. The decorator returns a version of the object that was wrapped.
One can have more than one decorator, and take the function to be modified as input.

For example:
```buildoutcfg
@decorator_1
@decorator_2
def function_one():
    pass

function_temp = decorator_2(function_one)
function_final = decorator_1(function_temp)
```

##### Example decorators found in Baobab
[@marshall_with](https://flask-restplus.readthedocs.io/en/stable/marshalling.html)

[@auth_required](https://flask-security-too.readthedocs.io/en/stable/patterns.html)

These can all be easily Googled for further clarity and descriptions as to how they modify the respective functions.

## Endpoints
The [API endpoint](https://smartbear.com/learn/performance-monitoring/api-endpoints/) is the end of a communication channel. When there are two interacting APIs, these interact with each other at the endpoint. This is the location from which APIs can access the network resources they need to carry out their functions.
APIs work using `requests` and `responses` in that they request information from a web application or web server and then receive a response. Endpoints send the requests and indicate where the resource lives. These are stored in the [routes.py](https://github.com/deep-learning-indaba/Baobab/blob/develop/api/app/routes.py) file in the [Baobab repository](https://github.com/deep-learning-indaba/Baobab).

## Models
These are an example of a Python object, specifically a database.

## Relational databases
The type of database we are interested in is called a relational database (and this is why ORM [Object Relational Mapping] is so relevant).
Relational databases set up relationships between items efficiently, and each data are stored in a table. The rows contain the items and the columns contain the properties of the items. The ORM (in our case, SQLAlchemy) is written in a language that is part of the web framework language (in our case, Python), allowing us to communicate with the database that is more familiar than SQL.

####Organisation of the data in a database versus a class:
**Class:**

|ClassName|
|---------|
|**id:** int|
|**name:** str|
|**descriptions:** str|

**Relational database:**

|ID:|Name:|Description:|
|---|---|---|
|INT|Char|VarChar|

### Database keys
Keys are fundamental in the creation of relationships between data (intra- and inter-tables). Further, they assist in maintaining uniqueness in a table; ensure consistent and valid data as well as allow for efficient data retrieval.

|Candidate keys (multiple, one can be a primary key)||
|--------------------------------------|---|
|**Primary keys**|**Alternate key:**|
|Uniquely identifies each record. Cannot be NULL.|Currently not selected as a primary key|
|Ensures entity integrity (ensures there are no duplicate records within the table)|**Unique key:** |
| |Similar to primary keys, but all for one null value|
| |No duplicates, useful for data validation|
| |Useful to place additional unique conditions on columns|
|**Composite keys:**| |
|a.k.a. Compound, composite keys| |
| More than one columns used to identify a unique value|

### Data types
These define the type of value that can be stored in a column. 
This summary of [PostgreSQL data types](https://www.postgresql.org/docs/9.5/datatype.html) will provide more information.
- Numeric: 
    - float, real, integers (no decimal, varying precision), decimal (fixed precision (p,s))
- Characters:
    - char, var_char, text
- Boolean: 
    - TRUE / FALSE
- JSON:
    - JavaScript Object Notation stores and exchanges data consisting of data types that are arrays or of attribute-value type. 
- XML:
    - Extensible markup language (creates information formats and electronically shares structured data via public and corporate networks)

## Universal Resource Locators
Protocols to locate and access information. These are used for communication between servers and clients. Examples include: [**HTTP**](https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol) (hypertext transfer protocols) and [FTP](https://en.wikipedia.org/wiki/File_Transfer_Protocol) (file transfer protocol for file transfers between client and server)
The general syntax is as you are used to seeing in your browser line:

`initiating protocol://web resource`

#### HTTP error codes
When there is communication between the **client** and **server**, [HTTP status codes](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes) are issued in response to a client’s request made to a server.
The 2XX codes refer to a successful communication in that the action was received, accepted and understood by the client
4XX codes refer to errors caused by the client. Common examples: 403 - client does not have access (the server understood the request, but there are inadequate permissions) and 404 (the resource isn’t found)
