# v0.2.0 --> Move databases (Postgres, MongoDB, DynamoDB) to their own Servers
---
Prod only, further ahead will figure out how to sync dev and "testing" (god help me) to the prod environment
- [X] pg_cron and update task priorities
- [X] MongoDB move to Atlas



# v0.3.0 --> Get rid of Flask-SQLAlchemy
- [ ] Use regular SQLAlchemy instead.



# v0.3.0 --> Migrate Databases

- [X] Countdowns -> SQLAlchemy
- [ ] Apartments -> SQLAlchemy
- [ ] Simplify Journal Entry MongoDB
- [ ] Get rid of Events dict
  - [ ] Maybe with Pydantic Models



# v0.4.0 --> Migrate Databases
- [ ] Alembic
- [ ] https://alembic.sqlalchemy.org/en/latest/tutorial.html


<!-- SMALL THINGS THAT NEED TO BE ADDRESSED -->
1. [ ] Take code out of `__init__.py` files
   1. [ ] Put them in `main.py` for the module or name of module
   2. [ ] Import the names in the `__init__.py` file for better top level imports
2. [ ] Main Site Navigation
   1. [ ] Put this on base page that all pages inherit from
   2. [ ] Inherit CSS as well
   3. [ ] Restructure site so that all apps are top level
      1. [ ] events
      2. [ ] countdowns
      3. [ ] journal
      4. [ ] habits

<!-- END OF SMALL THINGS -->

# v0.4.0 --> FastAPI
- FastAPI Course
API is being run on a different port/subdomain
api.ichrisbirch.com
https://adamtheautomator.com/nginx-subdomain/
https://hackprogramming.com/how-to-setup-subdomain-or-host-multiple-domains-using-nginx-in-linux-server/
https://blog.logrocket.com/how-to-build-web-app-with-multiple-subdomains-nginx/
https://stackoverflow.com/questions/64955127/nginx-multiple-node-apps-with-multiple-subdomains

- [ ] Update Nginx to serve both sites
  - [ ] 
- [ ] Update Endpoints to point to API
  - [ ] Apartments
  - [ ] Box-Packing
    - [ ] Rename `moving` to `box-packing`

FastAPI:
- [ ] Tasks
- [ ] Countdowns
- [ ] Events
- [ ] Journal
- [ ] Apartments
- [ ] Box Packing

Flask:
- [ ] Tasks
- [ ] Countdowns
- [ ] Events
- [ ] Journal
- [ ] Apartments
- [ ] Box Packing





# v0.3.1 --> Update nginx.conf
Use the new file so that the static files are served by nginx
Does this reach into all static folders?'






# v0.4.0 --> Backups
---
## Postgres

## MongoDB

## DynamoDB



# v0.5.0 --> User Login
---
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



# v0.6.0 --> WTForms
Is this something I want to do?



# v0.6.0 --> Testing
---
Udemy Class
- 
I have pytest book somewhere
Realpython
- Books on datapointchris.com
- pytest
- test driven dev in python



# v0.7.0 --> Typing
---
[Using mypy with an existing codebase — Mypy 0.942 documentation](https://mypy.readthedocs.io/en/stable/existing_code.html)
- [ ] Pydantic Models


# v0.8.0 --> Continuous Integration / Github Actions
---
Pre-commit - What is the difference between this and CI/CD

[Should You Use Github Actions for Continuous Integration (CI)? – CloudSavvy IT](https://www.cloudsavvyit.com/15499/should-you-use-github-actions-for-continuous-integration-ci/)
[How to Run Github Actions Builds on Your Own Servers With Self-Hosted Runners – CloudSavvy IT](https://www.cloudsavvyit.com/15503/how-to-run-github-actions-builds-on-your-own-servers-with-self-hosted-runners/)
[https://jacobtomlinson.dev/posts/2019/creating-github-actions-in-python/](https://jacobtomlinson.dev/posts/2019/creating-github-actions-in-python/)
[Ultimate CI Pipeline for All of Your Python Projects | by Martin Heinz | Mar, 2022 | Towards Data Science](https://towardsdatascience.com/ultimate-ci-pipeline-for-all-of-your-python-projects-27f9019ea71a)


# v0.9.0 --> Documentation
- Docs/notes for each page and function
- Hopefully a lot of this is done as I'm testing and doing type hinting



# v0.10.0 --> Re-structure CSS and Navigation
- [ ] CSS to inheret from main
  - [ ] Both the classes and site-wide variables
- [ ] There is a style of CSS naming convention, find that again.

@app.route('/favicon.ico')
def favicon():
    return send_file('static/favicon.ico')


# v0.11.0 --> Build Portfolio Page
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


===================================================
# Project Specific New / Future Possible Features
===================================================

## Euphoria
---
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



## * ~ New Project ~ *
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



## * ~ New Project ~ *
# Postgres Permissions Graphical Interface with Approvals
# Postgres Stats
- [ ] Make the SQL queries first
- [ ] Make each SQL query a function
- [ ] Be able to call these functions in API
- [ ] Tabbed interface for the different functions / stats
class PermissionRequest



## * ~ New Project ~ *
# Webstore Project
I want to make the sales follow a pattern that I specify, like sin waves or certain shapes, then see if the models can pick up on the shapes as a visual guide to accuracy.
Measuring their average or std or whatever over time and plotting it should give the right numbers.  See if the model can guess the correct shape.



## * ~ New Project ~ *
# Interview Star Questions
  - Have it talk to the command line version
  - Update Command line Version
  - Maybe use rich?
    - https://github.com/Textualize/rich