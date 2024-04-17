# TODO

- [Small Tasks](#small-tasks)
- [User Login](#user-login)
- [Random](#random)
- [Tasks](#tasks)
- [Infrastructure Management](#infrastructure-management)
- [WTForms](#wtforms)
- [Testing](#testing)
- [Logging](#logging)
- [Security](#security)
- [Performance Testing](#performance-testing)
- [Re-structure CSS and Navigation](#re-structure-css-and-navigation)
  - [Watch these videos](#watch-these-videos)
- [Build Portfolio Page](#build-portfolio-page)
- [Basic Main page and Portfolio](#basic-main-page-and-portfolio)
- [Employers](#employers)
- [ML Models](#ml-models)
- [Front-end Framework](#front-end-framework)
- [Project Specific](#project-specific)
  - [ichrisbirch](#ichrisbirch)
  - [Apartments](#apartments)
  - [Habits](#habits)
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
  - [Whylogs](#whylogs)

## Small Tasks

- [ ] Add button to submit github issue
  - [ ] Style the button as the other buttons with class "button box3d"
  - [ ] Clicking button should open pseudo-window
  - [ ] Auto-populate lots of information
    - [ ] time / date
    - [ ] browser information
    - [ ] page currently on
    - [ ] Have a template set up
    - [ ] Select from only a few types of issues
- [ ] (ops) Make validate html only validate pages that have been modified
  - [ ] pass files variable?
- [ ] (css) `_server_stats.scss` combine 3d text and 3d effect

## User Login

- [Flask Authentication By Example](https://developer.auth0.com/resources/guides/web-app/flask/basic-authentication)
- [GitHub - MushroomMaula/fastapi_login: FastAPI-Login tries to provide similar functionality as Flask-Login does.](https://github.com/MushroomMaula/fastapi_login)
- [How to Authenticate Users in Flask with Flask-Login](https://www.freecodecamp.org/news/how-to-authenticate-users-in-flask/)
- [Flask-Login — Flask-Login 0.7.0 documentation](https://flask-login.readthedocs.io/en/latest/)
- [GitHub - fastapi-users/fastapi-users: Ready-to-use and customizable users management for FastAPI](https://github.com/fastapi-users/fastapi-users)
- [Token-Based Authentication With Flask – Real Python](https://realpython.com/token-based-authentication-with-flask/)
- [How To Add Authentication to Your App with Flask-Login  | DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-add-authentication-to-your-app-with-flask-login)
- [GitHub - auth0/auth0-python: Auth0 SDK for Python](https://github.com/auth0/auth0-python)

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

## Random

- [ ] mypy - `--check-untyped-defs`
  - [ ] Add this option when ready to deal with other routes
- [ ] Make a startup script
  - [ ] So this can be started in Docker each time for testing
  - [ ] So it can be started on a fresh Postgres instance
- [ ] STATS
  - [ ] Move stats out of ichrisbirch
    - 1. Move them to ichrisbirch S3 bucket
    - 2. Create script to run them, similar to postgres backup script
    - 3. Run that script automatically with the backup on schedule
- [ ] Make sure fastapi is raising exceptions and not returning exceptions
- [ ] `etc/environment` in prod server for ENVIRONMENT variable
- [ ] Create `new-server` script that installs all the good stuff on new ec2 that can be run upon creation
  - [ ] Optionally, lock in an image with the stuff necessary to run server and use that image
- [ ] [GitHub - mkdocstrings/mkdocstrings: Automatic documentation from sources, for MkDocs.](https://github.com/mkdocstrings/mkdocstrings)
- [ ] [GitHub - zhanymkanov/fastapi-best-practices: FastAPI Best Practices and Conventions we used at our startup](https://github.com/zhanymkanov/fastapi-best-practices)
- [ ] [GitHub - Aeternalis-Ingenium/FastAPI-Backend-Template: A backend project template with FastAPI, PostgreSQL with asynchronous SQLAlchemy 2.0, Alembic for asynchronous database migration, and Docker.](https://github.com/Aeternalis-Ingenium/FastAPI-Backend-Template)
- [ ] [GitHub - igorbenav/FastAPI-boilerplate: An extendable async API using FastAPI, Pydantic V2, SQLAlchemy 2.0, PostgreSQL and Redis.](https://github.com/igorbenav/FastAPI-boilerplate)
- [ ] Change datetimes over to `Arrow`
- [ ] [Identity Federation for GitHub Actions on AWS | ScaleSec](https://scalesec.com/blog/identity-federation-for-github-actions-on-aws/)

## Tasks

- [ ] Alexa skill, use the to-do API to add a task
  - [ ] <https://github.com/johnwheeler/flask-ask>
  - [ ] I have a tutorial saved on the desktop for this
- [ ] Make an Alfred shortcut for todo
  - [ ] Using API most likely
- [ ] FIX: Catch error when priority is not specified in add task, currently there is a server error
  - [ ] This needs to be done in the form itself, before it gets sent
  - [ ] Either wtforms or some frontend framework with validation
- [ ] - [ ] /all
  - [ ] Count of various types of tasks left to do

## Infrastructure Management

- [ ] [How to Manage OpenStack Private Clouds Episode 1](https://www.patreon.com/posts/how-to-manage-1-78070880)

## WTForms

Is this something I want to do?

- [Introduction — WTForms-Alchemy 0.16.8 documentation](https://wtforms-alchemy.readthedocs.io/en/latest/introduction.html)
- [Quickstart — Flask-WTF Documentation (1.1.x)](https://flask-wtf.readthedocs.io/en/latest/quickstart/)

## Testing

[Mastering Integration Testing with FastAPI | Alex Jacobs](https://alex-jacobs.com/posts/fastapitests/)
[fastApi-Integration-tests/app/auth.py at main · alexjacobs08/fastApi-Integration-tests · GitHub](https://github.com/alexjacobs08/fastApi-Integration-tests/blob/main/app/auth.py)
[testcontainers 2.0.0 documentation](https://testcontainers-python.readthedocs.io/en/latest/postgres/README.html)
[LocalStack - A fully functional local cloud stack](https://localstack.cloud)
[How to test your FastAPI application - YouTube](https://www.youtube.com/watch?v=qC8AJzML3E4)
[TDD Tutorial](https://courses.cd.training/courses/tdd-tutorial)
[Patterns for Managing Source Code Branches](https://www.martinfowler.com/articles/branching-patterns.html)
[The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
[9 pytest tips and tricks to take your tests to the next level | Verdant Fox](https://verdantfox.com/blog/view/9-pytest-tips-and-tricks-to-take-your-tests-to-the-next-level)

[Unit Testing in Python -The Basics | The Startup](https://medium.com/swlh/unit-testing-in-python-basics-21a9a57418a0)

[End-to-end Testing with Python and Playwright — Six Feet Up](https://sixfeetup.com/blog/end-to-end-testing-python-playwright)

- Udemy Class
- I have pytest book somewhere
- Realpython
[Testing Flask Applications — Flask Documentation (2.2.x)](https://flask.palletsprojects.com/en/2.2.x/testing/)
- [GitHub - getsentry/responses: A utility for mocking out the Python Requests library.](https://github.com/getsentry/responses)
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
- [Don't mock Python's HTTPX](https://www.b-list.org/weblog/2023/dec/08/mock-python-httpx/)
- [“Don’t Mock What You Don’t Own” in 5 Minutes](https://hynek.me/articles/what-to-mock-in-5-mins/)

## Logging

[python - Using logging in multiple modules - Stack Overflow](https://stackoverflow.com/questions/15727420/using-logging-in-multiple-modules/15729700#15729700)

[Logging HOWTO — Python 3.11.2 documentation](https://docs.python.org/3/howto/logging.html#advanced-logging-tutorial)

[Good logging practice in Python – Fang-Pen's coding note](https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/)

[8 Advanced Python Logging Features that You Shouldn’t Miss | by Xiaoxu Gao | Towards Data Science](https://towardsdatascience.com/8-advanced-python-logging-features-that-you-shouldnt-miss-a68a5ef1b62d)

[Advanced Python Logging. Since you are here I am expecting that… | by Shanmukh | Analytics Vidhya | Medium](https://medium.com/analytics-vidhya/advance-python-logging-571912d3275f)

[Logging — The Underappreciated Art Form | by Tom Dickinson, PhD | Medium](https://www.tomkdickinson.co.uk/logging-the-underappreciated-art-form-40b8ec7add44)

[Python Logging: A Stroll Through the Source Code – Real Python](https://realpython.com/python-logging-source-code/)

[Python Logging: How to Write Logs Like a Pro! - YouTube](https://www.youtube.com/watch?v=pxuXaaT1u3k)

[Do not log](https://sobolevn.me/2020/03/do-not-log)

[GitHub - deviantony/docker-elk: The Elastic stack (ELK) powered by Docker and Compose.](https://github.com/deviantony/docker-elk)
[Open-Source Search Engine – Amazon OpenSearch Service Pricing – Amazon Web Services](https://aws.amazon.com/opensearch-service/pricing/)

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

## Performance Testing

[Your first test — Locust 2.15.1 documentation](https://docs.locust.io/en/stable/quickstart.html)

## Re-structure CSS and Navigation

### Watch these videos

- [The secret to mastering CSS layouts - YouTube](https://www.youtube.com/watch?v=vHuSz4fRM88)
-

- [ ] CSS to inherit from main
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

- [ ] [Reflection! Cool Effects with -webkit-box-reflect](https://dev.to/chokcoco/reflection-cool-effects-with-webkit-box-reflect-dpl)
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

[GitHub - Buuntu/fastapi-react: 🚀   Cookiecutter Template for FastAPI + React Projects.  Using PostgreSQL, SQLAlchemy, and Docker](https://github.com/Buuntu/fastapi-react)

[GitHub - Blazity/next-enterprise: 💼 An enterprise-grade Next.js boilerplate for high-performance, maintainable apps. Packed with features like Tailwind CSS, TypeScript, ESLint, Prettier, testing tools, and more to accelerate your development.](https://github.com/Blazity/next-enterprise)

Test this out on the portfolio page
resume page

Speed Dial component for frontend that has the error report and other useful shit

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

### Tracks

- [ ] Quote of the day!
- [ ] DELETE the Todo Part. This is being handled by `Tasks` and Obsidian for notes
- [ ] Re-design the tabs so that they are layered, eliminate tabs within tabs
- [ ] Daily Habits date changes at wrong time.  Set time to be local

### Events

- [ ] Add the Day of week to event date
- [ ] Delete Past events
  - [ ] Move them to history
  - [ ] Or mark them as past events
- [ ] Add time remaining for events
- [ ] Turn long URLs into `Event Link`
  - [ ] Only show URL if provided
  - [ ] Only show notes if provided

### Countdowns

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

[GitHub - kivy/kivy: Open source UI framework written in Python, running on Windows, Linux, macOS, Android and iOS](https://github.com/kivy/kivy)
[GitHub - TomSchimansky/CustomTkinter: A modern and customizable python UI-library based on Tkinter](https://github.com/TomSchimansky/CustomTkinter)

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

### Whylogs

[GitHub - whylabs/whylogs: An open-source data logging library for machine learning models and data pipelines. 📚 Provides visibility into data quality & model performance over time. 🛡️ Supports privacy-preserving data collection, ensuring safety & robustness. 📈](https://github.com/whylabs/whylogs)
