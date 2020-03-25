Glossary of useful concepts
============================
###### Narrowing the search space when you don’t even know what you don’t know

## Backend technology stack
This is divided into two sections. The technology stack is described first, as an introduction to the backend 
technologies used in Baobab. All words in **bold** are also defined within this document.

### Python
[Python](https://www.python.org/doc/essays/blurb/) is an interpreted object-orientated, high level programming language 
with dynamic typing.
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
- **Classes** are used in OOP in the creation of objects. 
- When comparing high-level to low-level languages, this refers to the level of abstraction. Each level is a step away 
from the base machine 
    - Abstraction: the degree to which the characteristics of an object are hidden in order to reduce complexity and 
    increase efficiency. The remaining object is a representation of the original with unwanted detail omitted
    - Higher level languages have greater levels of abstraction 

**3. Dynamic typing (i.e. _data types_)**
- As a point of [comparison](https://www.sitepoint.com/typing-versus-dynamic-typing/), static typed languages are Java,
 C and C++. Static typic requires the explicit declaration 
a variable before it is used: 

```buildoutcfg
/* Example of C code explicitly declaring a variable*/
static int num, sun; 
num = 5
sum = 10
sum = sum + num
```
- **Python** is a dynamic typed language, which means values can be assigned to variables before they are intialised:
```buildoutcfg
# Example of Python code (variable is assigned a value without first being explicitly declared)
num = 5 
sum = 10
sum = num + sum 
```
- In static typing, type checking is done at [compile-time](https://en.wikipedia.org/wiki/Compile_time) compared to 
[run-time](https://en.wikipedia.org/wiki/Runtime_(program_lifecycle_phase) for dynamic typed languages
## The database and ORM
Databases are used to organise and store information for easy information access and retrieval (essentially create, 
read, update and delete information). There are varying kinds of databases, viz. 
[spatial](https://www.tutorialspoint.com/Spatial-Databases), [non-relational](https://docs.microsoft.com/en-us/azure/architecture/data-guide/big-data/non-relational-data), [XML](https://www.tutorialspoint.com/xml/xml_databases.htm) and [graph](https://towardsdatascience.com/graph-databases-whats-the-big-deal-ec310b1bc0ed) databases.

The type of database we are interested in is a **relational database**.
[PostgreSQL](https://www.postgresqltutorial.com/what-is-postgresql/) is an fully object-relational database management 
system and is the chosen database for Baobab. SQL [(Structured Query Language)](http://www.sqlcourse.com/intro.html) is the language generally used for communication  with the database. However, SQL can be quite complicated, and tricky to work with if you are used to working in Python. Luckily, [ORM](https://www.fullstackpython.com/object-relational-mappers-orms.html) (object-relational mapper) exists for this very reason. ORM allows the programmer to communicate with the database in Python, instead of the database query language (or SQL) which can get quite complicated. [SQLAlchemy](https://towardsdatascience.com/sqlalchemy-python-tutorial-79a577141a91) is a library that allows us to communicate with the relational database more fluent in Python syntax by translating python classes to tables in the database and converts function calls to SQL statements. 

## Flask 
The **REST** **API** used is Flask. Flask is a Python micro [web-based framework](https://www.fullstackpython.com/web-frameworks.html) that is flexible and simple to implement when creating web-based applications such as Baobab. The main thing to remember about web-frameworks is that they are essentially code libraries that provide common methods / operations for building reliable, scalable, and maintainable web applications
The simplicity of Flask, compared to another framework such as [Django](https://www.djangoproject.com/), is particularly advantageous due to Baobab supporting remote contributors who may not have a lot of experience with web-application development. 

[Flask-RESTful](https://flask-restful.readthedocs.io/en/latest/) is a common flask extension, which works with 
existing ORM libraries and is used to make creating RESTful API calls simpler. An 
[API call](https://rapidapi.com/blog/api-glossary/api-call/) is essentially a process of sending an request having set up the **API** with the correct **endpoints**. 

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
    - Class: this is the creation of an idea which requires a collection of properties (attributes) pertaining to the idea. These can include a collection of function(s). Functions on a class are referred to as methods. The class will be instantiated repeatedly - without having to build the object from scratch each time.
- Classes take some getting used to, and there are many aspects like inheritance and  This [tutorial series on classes](https://www.digitalocean.com/community/tutorials/how-to-construct-classes-and-define-objects-in-python-3) is a good place to start.

## Clients and servers
- **Clients**
    - Computer hardware and/or software that accesses a service made available by a server, which is often on another computer. Clients access and modify resources (content)
- **Servers**
    - Manages access to a centralised resource / service in a network

## Decorators (in Python)
These are used in programming as wrappers around a function or object in order to modify it’s behaviour. Decorators are placed above a function with following characteristic syntax:
`@nameofdecorator`
Each decorator will modify an aspect of the original function or a class’s behaviour in a specific way without permanently modifying it. The decorator returns a version of the object that was wrapped.
One can have more than one decorator, and take the function to be modified as input.

For example:
```buildoutcfg
# Example of decorators being used to wrap a function
@decorator_1
@decorator_2
def function_one():
    pass

# The following code is equivalent to the above
function_temp = decorator_2(function_one)
function_final = decorator_1(function_temp)
```

##### Example decorators found in Baobab
[@marshall_with](https://flask-restplus.readthedocs.io/en/stable/marshalling.html)

[@auth_required](https://flask-security-too.readthedocs.io/en/stable/patterns.html)

These can all be easily Googled for further clarity and descriptions as to how they modify the respective functions.

## Endpoints
The [API endpoint](https://smartbear.com/learn/performance-monitoring/api-endpoints/) is the end of a communication 
channel. When there are two interacting APIs, these interact with each other at the endpoint. This is the location from 
which APIs can access the network resources they need to carry out their functions.
APIs work using `requests` and `responses` in that they request information from a web application or web server and 
then receive a response. Endpoints send the requests and indicate where the resource lives. These are stored in the 
[routes.py](https://github.com/deep-learning-indaba/Baobab/blob/develop/api/app/routes.py) file in the 
[Baobab repository](https://github.com/deep-learning-indaba/Baobab).

## Entitites
An entity is defined as any person, item, physical or virtual object that has a set of defining properties which need 
to be stored and may interact with and have relationships to other entities

## Models
- Models are Python object representations of some entity that gets mapped to and stored in the database
- These "relationships" are relevant in the context of **relational databases** defined below

## Relational databases
The type of database we are interested in is called a relational database (and this is why ORM 
[Object Relational Mapping] is so relevant).
Relational databases set up relationships between items efficiently, and each data are stored in a table. 
The rows contain the items and the columns contain the properties of the items. The ORM (in our case, SQLAlchemy) is 
written in a language that is part of the web framework language (in our case, Python), allowing us to communicate with 
the database that is more familiar than SQL.

####Organisation of the data in a database versus a class:
**Class:**

|ClassName|
|---------|
|**id:** int|
|**name:** str|
|**descriptions:** str|

**Relational database:**

- Each row in the database corresponds to a single object or instantiation of the class

|ID:|Name:|Description:|
|---|---|---|
|INT|Char|VarChar|

### Database keys
Keys are fundamental in the creation of relationships between data (intra- and inter-tables). Further, they assist in 
maintaining uniqueness in a table; ensure consistent and valid data as well as allow for efficient data retrieval.
- **Candidate keys:**
   - There are multiple keys in a database, one of which can be a primary key

- **Primary key:**
    - Uniquely identifies each record
    - Cannot be NULL
    - The primary key ensures there are no duplicate records within the table (entity integrity)
   
- **Alternate keys:**
    - These are the remaining candidate keys, none of which are currently selected as the primary key
- **Unique keys:**
    - This key is used to place additional unique conditions on columns
    - No duplicates in unique keys, and these are useful for data validation
    - Similar to primary keys, but allow for one NULL value
- **Composite keys:**
    - a.ka. compound keys
    - Composite keys are used when more than column is used to identify a value  

### Data types
These define the type of value that can be stored in a column. 
This summary of [PostgreSQL data types](https://www.postgresql.org/docs/9.5/datatype.html) will provide more information.
- Numeric: 
    - float, real, integers (no decimal, varying precision), decimal (fixed precision (p,s))
- Strings:
    - char, var_char, text
- Boolean: 
    - TRUE / FALSE
- [JSON](https://en.wikipedia.org/wiki/JSON):
    - JavaScript Object Notation stores and exchanges data consisting of data types that are arrays or of 
    attribute-value type. 
- [BLOB](https://en.wikipedia.org/wiki/Binary_large_object):
    - Binary Large OBject
    - Collection of [binary data](https://en.wikipedia.org/wiki/Binary_data) stored as a single entity in a database
     management system (in the case of Baobab, **PostgreSQL**)
    - These are typically images, audio or multimedia objects  

## URIs versus URLs
- [**URI:**](https://en.wikipedia.org/wiki/Uniform_Resource_Identifier) 
    - Universal Resource Identifier
    - A means of unambiguously identifying a resource (any identifiable thing - digitial, physical etc.) 
    using a string of characters that follow specific syntactical rules to ensure uniformity
    
- [**URL:**](https://en.wikipedia.org/wiki/URL)
    - Universal Resource Locator
    - Colloquially referred to as a web address
    - The URL specifies where the web resource is located on a web network and indicates the mechanism to access it
    
## Web protocols
Protocols to locate and access information. These are used for communication between servers and clients.
Two prominent examples are [**HTTP**](https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol) (hypertext transfer protocols)
  and [FTP](https://en.wikipedia.org/wiki/File_Transfer_Protocol) (file transfer protocol for file transfers between 
  client and server).
These protocols are specified in the **URL** using the general syntax as you are used to seeing in your browser line:

`initiating protocol://web resource`

#### HTTP error codes
When there is communication between the **client** and **server** using HTTP, 
[HTTP status codes](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes) are issued in response to a client’s 
request made to a server.
The 2XX codes refer to a successful communication in that the action was received, accepted and understood by the server
4XX codes refer to errors caused by the client. Common examples: 403 - client does not have access 
(the server understood the request, but there are inadequate permissions) and 404 (the resource isn’t found)
