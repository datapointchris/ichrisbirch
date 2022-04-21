# Move databases (Postgres, MongoDB, DynamoDB) to their own Servers
---
Prod only, further ahead will figure out how to sync dev and "testing" (god help me) to the prod environment
- [X] pg_cron and update task priorities
- [X] MongoDB move to Atlas
- [ ] DynamoDB Apartments (set up only)


# v0.3.0 --> Migrate Apartments to DynamoDB
---
1. "Schema" of the apartments
   1. Should the features each be a field or should there be a field with "features"?
2. Find scripts I've already written for other programs
   1. These are in Snippets Project
3. New DynamoDB Table and Connection



# v0.4.0 --> Backups
---
## Postgres

## MongoDB

## DynamoDB



# v0.5.0 --> User Login
---
- [ ] Create login for all apps as a main page.
	- [ ] [Flask User Accounts & Authentication in with Flask-Login](https://hackersandslackers.com/flask-login-user-authentication/)

- SSL for nginx
  - https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04
    - Step 6 - Securing the Application



# v0.6.0 --> Testing
---
Udemy Class
I have pytest book somewhere
Realpython



# v0.7.0 --> Typing
---
[Using mypy with an existing codebase — Mypy 0.942 documentation](https://mypy.readthedocs.io/en/stable/existing_code.html)



# v0.8.0 --> Continuous Integration / Github Actions
---

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



# v1.0.0 --> Basic Main page and Portfolio



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
- [ ] For every week that a task is on the list, it should get bumped an extra 5 points so that it's priority goes up and eventually it makes it to the top. 5 points X 20 == 100 so it would be top priority in 20 weeks ~ < 6 months.  Perfect.
- [ ] For each task on the today list, THERE CAN ONLY BE 5 AT A TIME, it goes by priority.  Only tasks with priority 0 get put on the list as extra and put to the top.  Priority 0 is Emergency and should be used very sparingly, to avoid daily bloat and slowdown.
- [ ] Description for each task can be markdown, and it will format it.
- [ ] Each task has a button that says `Tomorrow` so it can be moved to the next day if there are blockers.
- [ ] API with FastAPI
  - [ ] https://fastapi.tiangolo.com/tutorial/
- [ ] tasks.ichrisbirch.com
- [ ] Alexa skill, use the to-do API to add a task
- [ ] Make an Alfred shortcut for todo
	- [ ] This will change later when I do the todo in another way
	- [ ] Make app?
	- [ ] Make API and give it a simple HTTP request with the info
		- [ ] Authenticate?
		- [ ] Yes it will be a part of the login
- [ ] Make a "Completed This Month" List
	- [ ] Add things like courses done, big parts of projects, nagging chores
	- [ ] Anything that is good to know you got done, so you can add to the list
	- [ ] Okay, automate this thing so it saves the list every month
	- [ ] Probably a mongodb collection, one collection for each month and just a list of items, simple
- [ ] Graphs for all
- [ ] I think a better idea is to use a browser (javascript) based graphical if going beyond simple matplotlib graphs.  Stremlit requires it to have its own server, and python graphical libraries are not meant for the web.



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