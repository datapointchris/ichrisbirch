# TODO

- [Random](#random)
- [Continuous Integration / Github Actions](#continuous-integration--github-actions)
- [Documentation](#documentation)
  - [How To's](#how-tos)
  - [General Ideas](#general-ideas)
  - [Diagrams](#diagrams)
  - [Bluebook](#bluebook)
  - [Mkdocs](#mkdocs)
- [CSS files](#css-files)
- [Code Repo Structure](#code-repo-structure)
- [Tokei Output Charts](#tokei-output-charts)
- [All Tasks page improvments](#all-tasks-page-improvments)
  - [Add categories to tasks ENUM](#add-categories-to-tasks-enum)
  - [Create tasks/priority endpoint in tasks](#create-taskspriority-endpoint-in-tasks)
- [Upgrade to SQLAlchemy 2.0](#upgrade-to-sqlalchemy-20)
- [Create /autochore endpoint](#create-autochore-endpoint)
- [Add Events to API routes](#add-events-to-api-routes)
- [Add Countdowns to API routes](#add-countdowns-to-api-routes)
- [Infrastructure Management](#infrastructure-management)
- [User Login](#user-login)
- [WTForms](#wtforms)
- [Testing](#testing)
- [Logging](#logging)
- [Security](#security)
- [Re-structure CSS and Navigation](#re-structure-css-and-navigation)
- [Build Portfolio Page](#build-portfolio-page)
- [Basic Main page and Portfolio](#basic-main-page-and-portfolio)
- [Employers](#employers)
- [ML Models](#ml-models)
- [Front-end Framework](#front-end-framework)
- [Project Specific](#project-specific)
  - [ichrisbirch](#ichrisbirch)
  - [Apartments](#apartments)
  - [Habits](#habits)
  - [Tasks](#tasks)
  - [Tracks](#tracks)
  - [Events](#events)
  - [Countdowns](#countdowns)
  - [Box Moving](#box-moving)
  - [Journal](#journal)
- [Future Projects](#future-projects)
  - [Books](#books)
  - [Manage Github](#manage-github)
  - [Stable Diffusion](#stable-diffusion)
  - [Postgres Permissions Graphical Interface with Approvals / Stats](#postgres-permissions-graphical-interface-with-approvals--stats)
  - [Desktop App](#desktop-app)
  - [Webstore Project](#webstore-project)
  - [Interview Star Questions](#interview-star-questions)
  - [Learning](#learning)
  - [Goals](#goals)
  - [Overview](#overview)
  - [Ummmm and Like counter](#ummmm-and-like-counter)
  - [User Customization](#user-customization)

## Random
- [ ] Separate pytest and coverage in pre-commit and github-actions
- [ ] 

## Continuous Integration / Github Actions

[GitHub Actions Tutorial - Basic Concepts and CI/CD Pipeline with Docker - YouTube](https://www.youtube.com/watch?v=R8_veQiYBjI&list=WL&index=15&t=3s)

[GitHub Actions Tutorial | From Zero to Hero in 90 minutes (Environments, Secrets, Runners, etc) - YouTube](https://www.youtube.com/watch?v=TLB5MY9BBa4)

[How To Setup Github Actions For CI/CD - YouTube](https://www.youtube.com/watch?v=9flcoQ1R0Y4)

[Continuous Integration](https://www.martinfowler.com/articles/continuousIntegration.html#IntroducingContinuousIntegration)

[Patterns for Managing Source Code Branches](https://www.martinfowler.com/articles/branching-patterns.html)

[Python tox - Why You Should Use It and Tutorial](https://christophergs.com/python/2020/04/12/python-tox-why-use-it-and-tutorial/)

Pre-commit Possibilites:

- [X] Black
- [X] Flake8
- [X] isort
- [X] bandit
- [X] Interrogate
- [ ] pydoctest
- [ ] doctest
- [X] shellcheck
- [X] <https://github.com/dosisod/refurb>
- [X] <https://github.com/asottile/pyupgrade>
- [X] <https://github.com/python/mypy>

- [ ] Deploy action upon push of tags
- [ ] [A Complete Guide To Deploy GitHub Project on Amazon EC2 Using GitHub Actions and AWS CodeDeploy](https://dev.to/ankushbehera/a-complete-guide-to-deploy-github-project-on-amazon-ec2-using-github-actions-and-aws-codedeploy-3f0b)
- [ ] [Deploying with GitHub Actions - GitHub Docs](https://docs.github.com/en/actions/deployment/about-deployments/deploying-with-github-actions)
  - [ ] Actions
    - [ ] Create GitHub release
    - [ ] Deploy to ichrisbirch

[GitHub - appleboy/ssh-action: GitHub Actions for executing remote ssh commands.](https://github.com/appleboy/ssh-action)

[ssh deploy · Actions · GitHub Marketplace · GitHubtrucktruck](https://github.com/marketplace/actions/ssh-deploy)

[GitHub Actions: How to run SSH commands (without third-party actions) | Good Code Smell](https://blog.benoitblanchon.fr/github-action-run-ssh-commands/)

[Run server as systemd process & automate deployment with github actions - DEV](https://dev.to/lakhansamani/automate-server-deployment-with-systemd-github-actions-18od)

[Continuous Deployment using Github Actions | by Akshar Raaj | Medium](https://medium.com/@raaj.akshar/continuous-deployment-using-github-actions-37a7f5d7cb26)

[python - Github ssh-action configuration to deploy changes in django application - Stack Overflow](https://stackoverflow.com/questions/64295530/github-ssh-action-configuration-to-deploy-changes-in-django-application)

[Anyone using Github actions for your deployments? - Questions / Help - Elixir Programming Language Forum](https://elixirforum.com/t/anyone-using-github-actions-for-your-deployments/31210)

[Automatic Deployments With Nginx And GitHub Actions: A Detailed Guide | by Yash Prakash | Mar, 2023 | Level Up Coding](https://levelup.gitconnected.com/automatic-deployments-with-nginx-and-github-actions-a-detailed-guide-5505c074cc9f)

[Deploying to a server with GitHub Actions - Up and Running - Elixir Phoenix - YouTube](https://www.youtube.com/watch?v=gW1TDirJ5E4&list=PLZZkJeUxu6QmO83Z1esRhp3lOeaNKZuXY&index=8)

## Documentation

### How To's

Awesome documentation example for small project:
[Documentation — pypdf 3.5.1 documentation](https://pypdf.readthedocs.io/en/stable/dev/documentation.html)

[1. Software Documentation Template — Software Documentation 0.1 alpha documentation](https://software-documentation-template.readthedocs.io/en/latest/readme.html)

[A Guide to Writing Your First Software Documentation — SitePointSitePoint](https://www.sitepoint.com/writing-software-documentation/)

[How to Write Documentation For Your Next Software Development Project](https://www.freecodecamp.org/news/how-to-write-documentation-for-your-next-software-development-project/)

[Software Documentation Best Practices [With Examples] helpjuice-logo-0307896d1acd18c6a7f52c4256467fb6ca1007315c373af21357496e9ceb49e2](https://helpjuice.com/blog/software-documentation)

[Software Documentation Types and Best Practices | by AltexSoft Inc | Prototypr](https://blog.prototypr.io/software-documentation-types-and-best-practices-1726ca595c7f)

[Prepare the documentation for successful software project development](https://upplabs.com/blog/how-to-prepare-the-documentation-for-successful-software-project-development/)

[How to Write Technical Documentation With Empathy | by Edward Huang | Jan, 2023 | Better Programming](https://betterprogramming.pub/how-to-write-technical-documentation-with-empathy-f321104746f3)

### General Ideas

Docs/notes for each page and function

[Python's doctest: Document and Test Your Code at Once – Real Python](https://realpython.com/python-doctest/)
[Vale.sh - A linter for prose](https://vale.sh)

### Diagrams

[Online FlowChart & Diagrams Editor - Mermaid Live Editor](https://mermaid.live/edit)
[GitHub - mingrammer/diagrams: Diagram as Code for prototyping cloud system architectures](https://github.com/mingrammer/diagrams)

### Bluebook

This may actually be better for notes and personal information than for actual documentation inside of a project.

[GitHub - lyz-code/blue-book: My personal knowledge repository](https://github.com/lyz-code/blue-book)
[Write good documentation - The Blue Book](https://lyz-code.github.io/blue-book/documentation/)

### Mkdocs

[Build Your Python Project Documentation With MkDocs – Real Python](https://realpython.com/python-project-documentation-with-mkdocs/)

## CSS files

- [ ] Need to have reset
- [ ] Body in Apartments

## Code Repo Structure

- [ ] [GitHub Next | Visualizing a Codebase](https://githubnext.com/projects/repo-visualization/)

## Tokei Output Charts

- [ ] <https://github.com/laixintao/tokei-pie/blob/main/tokei_pie/main.py>
- [ ] Should I contribute or make my own?
- [ ] Make it easy to add another chart
- [ ] Model the structure of the output data so that it makes sense and is easy
  - [ ] Use Pydantic dataclasses to create the structure and for dot notation access
  - [ ] Good docs about the structure the objects are coming out as
  - [ ] Use streamlit for interactive charts?

TODO: [2022/11/05] - `etc/environment` in prod server for ENVIRONMENT variable
TODO: [2023/01/25] - Create `new-server` script that installs all the good stuff on new ec2 that can be run upon creation
TODO: [2023/01/25] - Optionally, lock in an image with the stuff necessary to run server and use that image

## All Tasks page improvments

- [ ] Add `Complete` button for all tasks
  - [ ] Should be for all of the tasks after the first 5
    - Sometimes tasks get completed early and they need to be marked as complete before in the top 5
  - [ ] Similar to the delete button
- [ ] Add filtering of `All | Completed | Not Completed` tasks.
  - [ ] Sort options as well?
- [ ] Add SEARCH capability!
- [ ] Delete for all tasks.  
  - [ ] Sometimes a task is added in error and needs to be deleted
  - [ ] This is on purpose instead of being able to edit tasks to keep honest
- [ ] Catch error when priority is not specified in add task, currently there is a server error
- [ ] Have add task redirect to the page that it was called from, instead of the priorities page.

### Add categories to tasks ENUM

- [ ] Compare this with the initial adding of the ENUM
  - [ ] Purchase
  - [ ] Work
  - [ ] Kitchen
  - [ ] Combine Learn = Research
    - [ ] Remove 'Research'

### Create tasks/priority endpoint in tasks

- [ ] Call this endpoint in the app instead of doing the query
  - This makes it so that other things can easily get the data with just an API call instead of constructing the query again

## Upgrade to SQLAlchemy 2.0

- [ ] [What's New in SQLAlchemy 2.0? - miguelgrinberg.com](https://blog.miguelgrinberg.com/post/what-s-new-in-sqlalchemy-2-0)
- [ ] Upgrade in poetry
- [ ] Check for syntax
- [ ]

## Create /autochore endpoint

- [ ] Simple storage of chores that need to be added to the priority list
  - [ ] Columns
    - Same as [tasks] columns
    - Additionally:
      - Add date for autochore
      - Priority to give it each time
      - How often to add it (days)

## Add Events to API routes

FastAPI:

- [ ] Events
- [ ] Cut a release
  - [ ] Notes

## Add Countdowns to API routes

FastAPI:

- [ ] Countdowns
- [ ] Cut a release
  - [ ] Notes

## Infrastructure Management

- [ ] [How to Manage OpenStack Private Clouds Episode 1](https://www.patreon.com/posts/how-to-manage-1-78070880)

## User Login

- [ ] Create login for all apps as a main page.
- [ ] [Basic Usage - FastAPI JWT Auth](https://indominusbyte.github.io/fastapi-jwt-auth/usage/basic/)
- [ ] [fastapi-github-actions-test/auth.py at master · rexsimiloluwah/fastapi-github-actions-test · GitHub](https://github.com/rexsimiloluwah/fastapi-github-actions-test/blob/master/src/routes/auth.py)
  - [ ] [Flask User Accounts & Authentication in with Flask-Login](https://hackersandslackers.com/flask-login-user-authentication/)
  - [ ] [Flask-Login — Flask-Login 0.7.0 documentation](https://flask-login.readthedocs.io/en/latest/)
  - [ ] [GitHub - maxcountryman/flask-login: Flask user session management.](https://github.com/maxcountryman/flask-login)
  - [ ] [Cookies with the Flask web framework | Verdant Fox](https://verdantfox.com/blog/view/cookies-with-the-flask-web-framework)

- SSL for nginx
  - [How To Serve Flask Applications with Gunicorn and Nginx on Ubuntu 18.04  | DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04)
    - Step 6 - Securing the Application

- Flask Admin -- NO
- [GitHub - flask-admin/flask-admin: Simple and extensible administrative interface framework for Flask](https://github.com/flask-admin/flask-admin)

- [Stop Using JSON Web Tokens For Authentication. Use Stateful Sessions Instead | by Francisco Sainz | Better Programming](https://betterprogramming.pub/stop-using-json-web-tokens-for-authentication-use-stateful-sessions-instead-c0a803931a5d)

- FastAPI Signup
- [python-api-examples/api.py at main · ChristopherGS/python-api-examples · GitHub](https://github.com/ChristopherGS/python-api-examples/blob/main/fastapi_project/app/api/api.py)

## WTForms

Is this something I want to do?

- [Introduction — WTForms-Alchemy 0.16.8 documentation](https://wtforms-alchemy.readthedocs.io/en/latest/introduction.html)
- [Quickstart — Flask-WTF Documentation (1.1.x)](https://flask-wtf.readthedocs.io/en/latest/quickstart/)

## Testing

[TDD Tutorial](https://courses.cd.training/courses/tdd-tutorial)
[Patterns for Managing Source Code Branches](https://www.martinfowler.com/articles/branching-patterns.html)
[The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
[9 pytest tips and tricks to take your tests to the next level | Verdant Fox](https://verdantfox.com/blog/view/9-pytest-tips-and-tricks-to-take-your-tests-to-the-next-level)

- Udemy Class
- I have pytest book somewhere
- Realpython
[Testing Flask Applications — Flask Documentation (2.2.x)](https://flask.palletsprojects.com/en/2.2.x/testing/)

- Books on datapointchris.com
- pytest
- test driven dev in python
- [Pytest with Marking, Mocking, and Fixtures in 10 Minutes | by Kay Jan Wong | Towards Data Science](https://towardsdatascience.com/pytest-with-marking-mocking-and-fixtures-in-10-minutes-678d7ccd2f70)
- [Writing tests for external API calls](https://www.cosmicpython.com/blog/2020-01-25-testing_external_api_calls.html)
- [Python pytest - The Blue Book](https://lyz-code.github.io/blue-book/coding/python/pytest/)
- [Test-Driven Development In Python // The power of red-green-refactor - YouTube](https://www.youtube.com/watch?v=B1j6k2j2eJg)
- [How To Write Unit Tests For Existing Python Code // Part 1 of 2 - YouTube](https://www.youtube.com/watch?v=ULxMQ57engo)
- [How To Write Unit Tests For Existing Python Code // Part 2 of 2 - YouTube](https://www.youtube.com/watch?v=NI5IGAim8XU)
- [End-To-End Tutorial For Pytest Fixtures With Examples](https://www.lambdatest.com/blog/end-to-end-tutorial-for-pytest-fixtures-with-examples/)
- [How To Use PyTest including Real Examples And Best Practices | by Eric Sales De Andrade | ITNEXT](https://itnext.io/how-to-use-pytest-including-real-examples-and-best-practices-11073e4fd514)
- DynamoDB
  - [pytest-dynamodb · PyPI](https://pypi.org/project/pytest-dynamodb/)
  - [Testing Boto3 with pytest Fixtures - Adam Johnson](https://adamj.eu/tech/2019/04/22/testing-boto3-with-pytest-fixtures/)
- MongoDB
  - [pytest-mongo · PyPI](https://pypi.org/project/pytest-mongo/)
  - [pytest-mongodb · PyPI](https://pypi.org/project/pytest-mongodb/)
- [Pytest for Beginners | TestDriven.io](https://testdriven.io/blog/pytest-for-beginners/)
- [Web Automation: Don't Use Selenium, Use Playwright](https://new.pythonforengineers.com/blog/web-automation-dont-use-selenium-use-playwright/)
- [Lean TDD | pythontest](https://pythontest.com/lean-tdd/)

## Logging

[python - Using logging in multiple modules - Stack Overflow](https://stackoverflow.com/questions/15727420/using-logging-in-multiple-modules/15729700#15729700)

[Logging HOWTO — Python 3.11.2 documentation](https://docs.python.org/3/howto/logging.html#advanced-logging-tutorial)

[Logging — The Underappreciated Art Form | by Tom Dickinson, PhD | Medium](https://www.tomkdickinson.co.uk/logging-the-underappreciated-art-form-40b8ec7add44)

[Python Logging: A Stroll Through the Source Code – Real Python](https://realpython.com/python-logging-source-code/)

[Python Logging: How to Write Logs Like a Pro! - YouTube](https://www.youtube.com/watch?v=pxuXaaT1u3k)

[Do not log](https://sobolevn.me/2020/03/do-not-log)

## Security

[API & Web Architecture - Security Best Practices | by Abdul Wahab | Medium](https://abdulrwahab.medium.com/api-web-architecture-security-best-practices-61522aff37be)
[Designing a secure API - DEV Community](https://dev.to/vaultree/designing-a-secure-api-4059)

- [ ] Make a new user for postgres?
  - [ ] Should I make a special user that connects to postgres?
  - [ ] Or should I use AWS IAM authentication with a password?
  - [ ] But I need a user to do admin stuff, I guess postgres is okay for that
  - [ ] But should definitely be a separate user for the app
    - [ ] They don't need permission to:
      - [ ] postgres database
      - [ ] pgcron
      - [ ] ONLY to `ichrisbirch` db

## Re-structure CSS and Navigation

- [ ] CSS to inheret from main
  - [ ] Both the classes and site-wide variables
- [ ] There is a style of CSS naming convention, find that again.
- [ ] <https://github.com/bem/bem-sdk#naming>
- [ ] <https://en.bem.info/toolbox/>
- [ ] <https://en.bem.info/methodology/css/>
- [ ]

@app.route('/favicon.ico')
def favicon():
    return send_file('static/favicon.ico')

## Build Portfolio Page

- [ ] code this entirely by hand, using small code packages
  - [ ] Dataset
  - [ ] Dataset-orm
- [ ] Use templates for everything

## Basic Main page and Portfolio

- Portfolio
  - [ ] Of course have the stupid carousel portfolio
    - [ ] When hover on project, get the 'highlights' reel.

## Employers

- Super awesome employers only link
  - Enter their super special employer code
  - Customized short video (my own voice from computer)

## ML Models

- [ ] API
- [ ] Corresponding Flask interface
  - [ ] Choose models
  - [ ] Choose dataset
    - [ ] Use the scikit-learn toy datasets to get a feel
  - [ ] Graphing, maybe this is part of Front-End
<https://towardsdatascience.com/how-to-properly-ship-and-deploy-your-machine-learning-model-8a8664b763c4>
<https://testdriven.io/blog/fastapi-machine-learning/>

## Front-end Framework

Test this out on the portfolio page
resume page

## Project Specific

### ichrisbirch

- [ ] Command to bring up the menu, like in github
- [ ] Make a home tab that is present in every page somewhere
- [ ] `Report an Issue` button at the bottom or floating somewhere in the footer or nav that pops up a form in the middle that they submit easily and it goes to the correct repository as an issue on github and auto assigns me and I get an email.
- [ ] Automated web testing of all the buttons and forms?
- [ ] Nav on the bottom that when you click it, it comes up with rotating gears on each side.
  - [ ] [Floating Buttons](https://codepen.io/rashiq/pen/eqGEzw)
  - [ ] [Animated BottomBar Experiment (CSS Transitions only)](https://codepen.io/chrisbautista/pen/NWXjqLN)
- [ ] GEARS
  - [ ] <https://webdevtrick.com/cog-loading-animation/>
  - [ ] <https://css-challenges.com/rotating-gears/>
  - [ ] <https://www.script-tutorials.com/demos/247/index.html>
  - [ ] <https://jsfiddle.net/LukaszWiktor/4qpcqymp/>
  - [ ] <https://codepen.io/alextebbs/pen/tHhrz>
  - [ ] <https://www.script-tutorials.com/css3-animated-gears/>
- [ ] Integrate with bookmarks
  - [ ] Article of the Day

### Apartments

### Habits

<https://github.com/flatpickr/flatpickr>

Ranking
 [Slider with value and ruler](https://codepen.io/thebabydino/pen/RwjWrKz)

### Tasks

- [ ] Remove the Fake Tasks and Delete Tasks
- [ ] Chart.js
- [ ] <https://blog.ruanbekker.com/blog/2017/12/14/graphing-pretty-charts-with-python-flask-and-chartjs/>
- [ ] Each task has a button that says `Tomorrow` so it can be moved to the next day if there are blockers.
- [ ] API with FastAPI
- [ ] FastAPI and Flask together?  Maybe not possible
  - [ ] <https://fastapi.tiangolo.com/tutorial/>
- [ ] tasks.ichrisbirch.com
- [ ] Make a "Completed This Month" List
  - [ ] Add things like courses done, big parts of projects, nagging chores
  - [ ] Anything that is good to know you got done, so you can add to the list
  - [ ] Okay, automate this thing so it saves the list every month
  - [ ] Probably a mongodb collection, one collection for each month and just a list of items, simple
- [ ] Alexa skill, use the to-do API to add a task
- [ ] Make an Alfred shortcut for todo
  - [ ] Using API most likely

### Tracks

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

### Box Moving

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

### Journal

- [ ] Default Template to give a start
  EX: `3 Things Thankful:`
      (Write here)
      `5 New Ideas:`
      (Write here)
- [ ] Weekly / Monthly Themes
  - [ ] Integrated with the templates
  - [ ] Possibly even a color theme for effect
  - [ ] Music theme for repetition

## Future Projects

### Books

<https://stackabuse.com/file-management-with-aws-s3-python-and-flask/>
<https://stackoverflow.com/questions/73211035/how-do-i-configure-nginx-to-serve-static-files-from-an-aws-s3-bucket>

### Manage Github

Use API to pull github projects
If they have issues that need taken care of display those.
Make a link to go to the issues.
Each github project should have:

- Name
- Link
- local directory {projects, apps, tutorials, etc}
This should have an API that I can call in a python script to download all of them.
Upon opening it should check if there is a new github repository and alert me so that I can properly add it.

### Stable Diffusion

Because why not?
<https://github.com/huggingface/diffusers>

### Postgres Permissions Graphical Interface with Approvals / Stats

- [ ] Make the SQL queries first
- [ ] Make each SQL query a function
- [ ] Be able to call these functions in API
- [ ] Tabbed interface for the different functions / stats
- [ ] class PermissionRequest
- [ ] <https://github.com/AykutSarac/jsoncrack.com?utm_source=substack&utm_medium=email>

### Desktop App

<https://github.com/TomSchimansky/CustomTkinter>

### Webstore Project

I want to make the sales follow a pattern that I specify, like sin waves or certain shapes, then see if the models can pick up on the shapes as a visual guide to accuracy.
Measuring their average or std or whatever over time and plotting it should give the right numbers.  See if the model can guess the correct shape.

### Interview Star Questions

- Have it talk to the command line version
- Update Command line Version
- Maybe use rich?
  - <https://github.com/Textualize/rich>

### Learning

### Goals

### Overview

### Ummmm and Like counter

[Building a ChatGPT-based AI Assistant with Python using OpenAI APIs](https://faizanbashir.me/building-a-chatgpt-based-ai-assistant-with-python-speech-to-text-and-text-to-speech-using-openai-apis)

[GitHub - sozykin/ml_fastapi_tests](https://github.com/sozykin/ml_fastapi_tests)

[GitHub - faizanbashir/speaking-chatgpt](https://github.com/faizanbashir/speaking-chatgpt)

Submit an audio recording and it will return the count of 'ummm' and 'like', 'ya know'
You can select which common phrases you want to find in the audio

<https://platform.openai.com/docs/guides/speech-to-text>

### User Customization

- color scheme
- timezone
- session / cookies
  - I don't know anything about this
