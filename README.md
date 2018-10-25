# Universal-Mapper
Mapping tool for different standardized or 'in-house' code systems.

--

##### Currently in user feedback development phase

--

#### Introduction 

A specific tool was requested for transforming codes based on certain code system to another system. The plinth of this work originated from public demand to standardize coding system used in nation-wide pathologist community called SNOMED II. It is hierarchical coding system for pathological findings (morphologies in cells, tissues and organs) and finding sites (topographies; anatomic terms of targetted organ).

There is a period of transition to newer graph-based coding system called Snomed-CT, which is wider and more complex coding system including also relationships and high level description logic. It is considered to be the most comprehensive, multilingual clinical healthcare terminology in the world also covering other than pathological concepts from laboratory tests to socioeconomical statuses.

This tool can be used with any other code system which consists of code and term pairs (concepts).

--

#### Technologies

This software is based on free license technology, mainly Apache 2.0. It is constructed on top of Python (3.x.x) using Flask framework with Jinja template engine, Werkzeug toolkit and SQLAlchemy ORM. Front-end is pure HTML5, CSS and JavaScript with JQuery, Bootstrap v4 and DataTables.

[External Snomed-CT browser](https://github.com/IHTSDO/sct-browser-frontend) is borrowed from [IHTSDO](https://github.com/IHTSDO) and modified to work embedded on the site.

--

#### Primary To-do's

* Active Directory authentication and mPollux API
* Example database for live demo
* Snomed-CT relationship mapping utilising Neo4J graph database