
- [-- Misc --](#---misc---)
- [Sitewide $PROJECT variable](#sitewide-project-variable)
  - [CSS files](#css-files)
  - [Code Repo Structure](#code-repo-structure)
  - [Tokei Output Charts](#tokei-output-charts)
- [v0.5.1 --> {Patch} Add "notes" field to tasks](#v051----patch-add-notes-field-to-tasks)
- [v0.5.2 --> {Patch} Use Enum for task categories](#v052----patch-use-enum-for-task-categories)
- [v0.5.3 --> {Patch} Add 'Complete Task' button on All Tasks page](#v053----patch-add-complete-task-button-on-all-tasks-page)
- [v0.5.4 --> {Patch} Create /priority endpoint in tasks](#v054----patch-create-priority-endpoint-in-tasks)
- [v0.6.0 --> Rename entire project to ichrisbirch](#v060----rename-entire-project-to-ichrisbirch)
- [v0.7.0 --> Add Countdowns to API routes](#v070----add-countdowns-to-api-routes)
- [v0.7.0 --> Add Events to API routes](#v070----add-events-to-api-routes)
- [v0.7.0 --> Continuous Integration / Github Actions](#v070----continuous-integration--github-actions)
- [v0.4.0 --> Backups](#v040----backups)
- [v0.5.0 --> User Login](#v050----user-login)
- [v0.6.0 --> WTForms](#v060----wtforms)
- [v0.7.0 --> Testing](#v070----testing)
- [v0.8.0 --> Logging](#v080----logging)
- [v0.9.0 --> Security](#v090----security)
- [v0.10.0 --> Typing](#v0100----typing)
- [v0.11.0 --> Documentation](#v0110----documentation)
- [v0.12.0 --> Re-structure CSS and Navigation](#v0120----re-structure-css-and-navigation)
- [v0.13.0 --> Build Portfolio Page](#v0130----build-portfolio-page)
- [v1.0.0 --> Basic Main page and Portfolio](#v100----basic-main-page-and-portfolio)
- [v1.1.0 --> Employers](#v110----employers)
- [v1.1.0 --> ML Models](#v110----ml-models)
- [v1.1.0 --> Front-end Framework](#v110----front-end-framework)
- [# Project Specific](#-project-specific)
  - [Euphoria](#euphoria)
  - [Apartments](#apartments)
  - [Tasks](#tasks)
  - [Tracks](#tracks)
    - [Events](#events)
    - [Countdowns](#countdowns)
  - [Box Moving](#box-moving)
  - [Journal](#journal)
- [# Future Projects](#-future-projects)
  - [Books](#books)
  - [Manage Github](#manage-github)
  - [Postgres Permissions Graphical Interface with Approvals / Stats](#postgres-permissions-graphical-interface-with-approvals--stats)
  - [Webstore Project](#webstore-project)
  - [Interview Star Questions](#interview-star-questions)
  - [Learning](#learning)
  - [Goals](#goals)
  - [Overview](#overview)
  - [Budget](#budget)
  - [Time Tracker](#time-tracker)
  - [Deep Dream](#deep-dream)
  - [Ummmm and Like counter](#ummmm-and-like-counter)
  - [User Customization](#user-customization)
  - [Git Graph Maker](#git-graph-maker)



# -- Misc --
# Sitewide $PROJECT variable

## CSS files
  - [ ] Need to have reset
  - [ ] Body in Apartments
## Code Repo Structure
  - [ ] https://githubnext.com/projects/repo-visualization/
## Tokei Output Charts
  - [ ] https://github.com/laixintao/tokei-pie/blob/main/tokei_pie/main.py
  - [ ] Should I contribute or make my own?
  - [ ] Make it easy to add another chart
  - [ ] Model the structure of the output data so that it makes sense and is easy
    - [ ] Use Pydantic dataclasses to create the structure and for dot notation access
    - [ ] Good docs about the structure the objects are coming out as
    - [ ] Use streamlit for interactive charts?

 TODO: [2022/11/02] - Add the release versions here then move to CHANGELOG.md

# v0.5.1 --> {Patch} Add "notes" field to tasks
- [ ] !! __MAKE NOTES__ !!
- [ ] SQLAlchemy model
- [ ] Pydantic model
- [ ] Migration
- [ ] Cut a release
  - [ ] Make notes



# v0.5.2 --> {Patch} Use Enum for task categories
- [ ] !! __MAKE NOTES__ !!
- [ ] https://realpython.com/python-enum/
- [ ] https://docs.python.org/3/library/enum.html
- [ ] SQLAlchemy model
- [ ] Pydantic model
- [ ] Migration
- [ ] Cut a release
  - [ ] Make notes



# v0.5.3 --> {Patch} Add 'Complete Task' button on All Tasks page
- [ ] Should be for all of the tasks after the first 5
  - Sometimes tasks get completed early and they need to be marked as complete before in the top 5
  - [ ] Similar to the delete button



# v0.5.4 --> {Patch} Create /priority endpoint in tasks
- [ ] Call this endpoint in the app instead of doing the query
  - This makes it so that other things can easily get the data with just an API call instead of constructing the query again



# v0.6.0 --> Rename entire project to ichrisbirch
FastAPI:
- [ ] nginx files
- [ ] supervisor files
- [ ] folders
- [ ] name of keys
- [ ] name of security group
- [ ] name of mongo servers
- [ ] Do a grep for all things euphoria


# v0.7.0 --> Add Countdowns to API routes
FastAPI:
- [ ] Countdowns
- [ ] Cut a release
  - [ ] Notes



# v0.7.0 --> Add Events to API routes
FastAPI:
- [ ] Events
- [ ] Cut a release
  - [ ] Notes


# v0.7.0 --> Continuous Integration / Github Actions
Pre-commit - What is the difference between this and CI/CD
https://christophergs.com/python/2020/04/12/python-tox-why-use-it-and-tutorial/
https://www.youtube.com/watch?v=TLB5MY9BBa4
https://github.blog/2022-06-03-a-beginners-guide-to-ci-cd-and-automation-on-github/
https://lab.github.com/githubtraining/devops-with-github-actions
[Should You Use Github Actions for Continuous Integration (CI)? – CloudSavvy IT](https://www.cloudsavvyit.com/15499/should-you-use-github-actions-for-continuous-integration-ci/)
[How to Run Github Actions Builds on Your Own Servers With Self-Hosted Runners – CloudSavvy IT](https://www.cloudsavvyit.com/15503/how-to-run-github-actions-builds-on-your-own-servers-with-self-hosted-runners/)
[https://jacobtomlinson.dev/posts/2019/creating-github-actions-in-python/](https://jacobtomlinson.dev/posts/2019/creating-github-actions-in-python/)
[Ultimate CI Pipeline for All of Your Python Projects | by Martin Heinz | Mar, 2022 | Towards Data Science](https://towardsdatascience.com/ultimate-ci-pipeline-for-all-of-your-python-projects-27f9019ea71a)
https://towardsdatascience.com/ultimate-setup-for-your-next-python-project-179bda8a7c2c
https://ravilach.medium.com/continuous-integration-developer-getting-started-guide-zero-to-pipeline-4a59553617f3
https://betterprogramming.pub/
https://towardsdatascience.com/simplify-your-python-code-automating-code-complexity-analysis-with-wily-5c1e90c9a485
https://www.youtube.com/watch?v=R8_veQiYBjI&list=WL&index=15&t=3s




# v0.4.0 --> Backups
- [ ] Postgres
- [ ] MongoDB
- [ ] DynamoDB
- [X] Code
  - [X] Github



# v0.5.0 --> User Login
- [ ] Create login for all apps as a main page.
	- [ ] [Flask User Accounts & Authentication in with Flask-Login](https://hackersandslackers.com/flask-login-user-authentication/)
	- [ ] https://flask-login.readthedocs.io/en/latest/
	- [ ] https://github.com/maxcountryman/flask-login

- SSL for nginx
  - https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04
    - Step 6 - Securing the Application

- Flask Admin -- NO
- https://github.com/flask-admin/flask-admin

- JSON Web Tokens
https://betterprogramming.pub/stop-using-json-web-tokens-for-authentication-use-stateful-sessions-instead-c0a803931a5d

- FastAPI Signup
- https://github.com/ChristopherGS/python-api-examples/blob/main/fastapi_project/app/api/api.py


# v0.6.0 --> WTForms
Is this something I want to do?
- https://wtforms-alchemy.readthedocs.io/en/latest/introduction.html
- https://flask-wtf.readthedocs.io/en/latest/quickstart/



# v0.7.0 --> Testing
Udemy Class
- 
I have pytest book somewhere
Realpython
https://flask.palletsprojects.com/en/2.2.x/testing/
- Books on datapointchris.com
- pytest
- test driven dev in python
- https://www.cosmicpython.com/blog/2020-01-25-testing_external_api_calls.html
- https://lyz-code.github.io/blue-book/coding/python/pytest/
- https://www.youtube.com/watch?v=B1j6k2j2eJg
- https://www.youtube.com/watch?v=ULxMQ57engo
- https://www.youtube.com/watch?v=NI5IGAim8XU
- https://www.lambdatest.com/blog/end-to-end-tutorial-for-pytest-fixtures-with-examples/
- https://itnext.io/how-to-use-pytest-including-real-examples-and-best-practices-11073e4fd514
- DynamoDB
  - https://pypi.org/project/pytest-dynamodb/
  - https://adamj.eu/tech/2019/04/22/testing-boto3-with-pytest-fixtures/
- MongoDB
  - https://pypi.org/project/pytest-mongo/
  - https://pypi.org/project/pytest-mongodb/
- https://testdriven.io/blog/pytest-for-beginners/


# v0.8.0 --> Logging
https://medium.com/@petefison/logging-in-python-doesnt-get-simpler-than-this-50a7f24af1f4
https://www.palkeo.com/en/blog/python-logging.html
https://guicommits.com/how-to-log-in-python-like-a-pro/
https://stackoverflow.com/questions/15727420/using-logging-in-multiple-modules/15729700#15729700
https://docs.python.org/3/howto/logging.html#advanced-logging-tutorial
https://www.tomkdickinson.co.uk/logging-the-underappreciated-art-form-40b8ec7add44


# v0.9.0 --> Security
https://abdulrwahab.medium.com/api-web-architecture-security-best-practices-61522aff37be
https://dev.to/vaultree/designing-a-secure-api-4059


# v0.10.0 --> Typing
[Using mypy with an existing codebase — Mypy 0.942 documentation](https://mypy.readthedocs.io/en/stable/existing_code.html)
- [ ] Pydantic Models




# v0.11.0 --> Documentation
- Docs/notes for each page and function
- Hopefully a lot of this is done as I'm testing and doing type hinting
- https://realpython.com/python-doctest/
- https://github.com/lyz-code/blue-book
- https://lyz-code.github.io/blue-book/documentation/
https://realpython.com/python-project-documentation-with-mkdocs/
- Code and architecture Diagramming
- https://github.com/mingrammer/diagrams
https://vale.sh
- https://software-documentation-template.readthedocs.io/en/latest/readme.html
- https://www.sitepoint.com/writing-software-documentation/
- https://www.freecodecamp.org/news/how-to-write-documentation-for-your-next-software-development-project/
- https://helpjuice.com/blog/software-documentation
- https://blog.prototypr.io/software-documentation-types-and-best-practices-1726ca595c7f
- https://upplabs.com/blog/how-to-prepare-the-documentation-for-successful-software-project-development/
- 

# v0.12.0 --> Re-structure CSS and Navigation
- [ ] CSS to inheret from main
  - [ ] Both the classes and site-wide variables
- [ ] There is a style of CSS naming convention, find that again.
- [ ] https://github.com/bem/bem-sdk#naming
- [ ] https://en.bem.info/toolbox/
- [ ] https://en.bem.info/methodology/css/
- [ ] 

@app.route('/favicon.ico')
def favicon():
    return send_file('static/favicon.ico')


# v0.13.0 --> Build Portfolio Page
- [ ] code this entirely by hand, using small code packages
  - [ ] Dataset
  - [ ] Dataset-orm
- [ ] Use templates for everything


# v1.0.0 --> Basic Main page and Portfolio
- Portfolio
  - [ ] Of course have the stupid carousel portfolio
    - [ ] When hover on project, get the 'highlights' reel.



# v1.1.0 --> Employers
- Super awesome employers only link
  - Enter their super special employer code
  - Customized short video (my own voice from computer)



# v1.1.0 --> ML Models
- [ ] API
- [ ] Corresponding Flask interface
  - [ ] Choose models
  - [ ] Choose dataset
    - [ ] Use the scikit-learn toy datasets to get a feel
  - [ ] Graphing, maybe this is part of Front-End
https://towardsdatascience.com/how-to-properly-ship-and-deploy-your-machine-learning-model-8a8664b763c4
https://testdriven.io/blog/fastapi-machine-learning/



# v1.1.0 --> Front-end Framework
Test this out on the portfolio page
- resume page


==================
# Project Specific
==================

## Euphoria
- [ ] Command to bring up the menu, like in github
- [ ] Make a home tab that is present in every page somewhere
- [ ] `Report an Issue` button at the bottom or floating somewhere in the footer or nav that pops up a form in the middle that they submit easily and it goes to the correct repository as an issue on github and auto assigns me and I get an email.
- [ ] Automated web testing of all the buttons and forms?
- [ ] Nav on the bottom that when you click it, it comes up with rotating gears on each side.
	- [ ] [Floating Buttons](https://codepen.io/rashiq/pen/eqGEzw)
	- [ ] [Animated BottomBar Experiment (CSS Transitions only)](https://codepen.io/chrisbautista/pen/NWXjqLN)
- [ ] GEARS
  - [ ] https://webdevtrick.com/cog-loading-animation/
  - [ ] https://css-challenges.com/rotating-gears/
  - [ ] https://www.script-tutorials.com/demos/247/index.html
  - [ ] https://jsfiddle.net/LukaszWiktor/4qpcqymp/
  - [ ] https://codepen.io/alextebbs/pen/tHhrz
  - [ ] https://www.script-tutorials.com/css3-animated-gears/
- [ ] Integrate with bookmarks
  - [ ] Article of the Day


## Apartments
Ranking
	[Slider with value and ruler](https://codepen.io/thebabydino/pen/RwjWrKz)



## Tasks
- [ ] Remove the Fake Tasks and Delete Tasks
- [ ] Chart.js
- [ ] https://blog.ruanbekker.com/blog/2017/12/14/graphing-pretty-charts-with-python-flask-and-chartjs/
- [ ] Each task has a button that says `Tomorrow` so it can be moved to the next day if there are blockers.
- [ ] API with FastAPI
- [ ] FastAPI and Flask together?  Maybe not possible
  - [ ] https://fastapi.tiangolo.com/tutorial/
- [ ] tasks.ichrisbirch.com
- [ ] Make a "Completed This Month" List
	- [ ] Add things like courses done, big parts of projects, nagging chores
	- [ ] Anything that is good to know you got done, so you can add to the list
	- [ ] Okay, automate this thing so it saves the list every month
	- [ ] Probably a mongodb collection, one collection for each month and just a list of items, simple
- [ ] Alexa skill, use the to-do API to add a task
- [ ] Make an Alfred shortcut for todo
  - [ ] Using API most likely




## Tracks
- [ ] Quote of the day!
- [ ] DELETE the Todo Part. This is being handled by `Tasks` and Obsidian for notes
- [ ] Re-design the tabs so that they are layered, eliminate tabs within tabs
- [ ] Daily Habits date changes at wrong time.  Set time to be local

### Events
- [ ] Add the Day of week to event date
- [ ] Delete Past events
- [ ] Add time remaining for events
- [ ] Turn long URLs into `Event Link` 

### Countdowns
- [ ] Automatically put a countdown for any Event that I am attending


## Box Moving
- [ ] Cascade on delete to delete box items
- [ ] Add box # to search results
- [ ] Make check boxes bigger on main page
- [ ] Display block to have the whole thing be clickable
- [ ] Make box selector menu bigger
- [ ] Fix internal search error 500 with special characters
- [ ] Make the search a fuzzy search
- [ ] Make search box focus on load
- [ ] Make search results clickable
- [ ] Edit box name


## Journal
- [ ] Default Template to give a start
  EX: `3 Things Thankful:`
      (Write here)
      `5 New Ideas:`
      (Write here)
- [ ] Weekly / Monthly Themes
  - [ ] Integrated with the templates
  - [ ] Possibly even a color theme for effect
  - [ ] Music theme for repetition 


=================
# Future Projects
=================

## Books
https://stackabuse.com/file-management-with-aws-s3-python-and-flask/
https://stackoverflow.com/questions/73211035/how-do-i-configure-nginx-to-serve-static-files-from-an-aws-s3-bucket

## Manage Github
Use API to pull github projects
If they have issues that need taken care of display those.
Make a link to go to the issues.
Each github project should have:
- Name
- Link
- local directory {projects, apps, tutorials, etc}
This should have an API that I can call in a python script to download all of them.
Upon opening it should check if there is a new github repository and alert me so that I can properly add it.



## Postgres Permissions Graphical Interface with Approvals / Stats
- [ ] Make the SQL queries first
- [ ] Make each SQL query a function
- [ ] Be able to call these functions in API
- [ ] Tabbed interface for the different functions / stats
- [ ] class PermissionRequest
- [ ] https://github.com/AykutSarac/jsoncrack.com?utm_source=substack&utm_medium=email




## Webstore Project
I want to make the sales follow a pattern that I specify, like sin waves or certain shapes, then see if the models can pick up on the shapes as a visual guide to accuracy.
Measuring their average or std or whatever over time and plotting it should give the right numbers.  See if the model can guess the correct shape.



## Interview Star Questions
  - Have it talk to the command line version
  - Update Command line Version
  - Maybe use rich?
    - https://github.com/Textualize/rich



## Learning



## Goals



## Overview



## Budget



## Time Tracker
Fields:
- Description
- Category
- Duration
- Timestamp (inserted automatically, for future use)

On the main summary/overview page, should display top 3/5 activities that take time over previous selectable timespan.  Selectable to particular categories and/or subcategories.  Also able to exclude categories and/or subcategories.
Kind of like budgeting, but only for time.



## Deep Dream
https://www.tensorflow.org/tutorials/generative/deepdream



## Ummmm and Like counter
- submit an audio recording and it will return the count of 'ummm' and 'like', 'ya know'
- You can select which common phrases you want to find in the audio
- 



## User Customization
- color scheme
- timezone
- session / cookies
  - I don't know anything about this


## Git Graph Maker
- functions that make commits and try with different methods
  - merge
  - merge with squash
  - rebase
  - rebase with squash
  - create release
  - tag release