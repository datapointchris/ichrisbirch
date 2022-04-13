




## How it Works

### Backups
1. Install AWS-CLI
2. `aws configure` - Use credentials for 
MongDB Backup:
https://www.cloudsavvyit.com/6059/how-to-set-up-automated-mongodb-backups-to-s3/

Postgres Backup:









======== NOT README STUFF ========

# Use Python 3.10.1 everywhere

# TODO

- Use config parameters for dev vs production
  - https://dlabs.ai/blog/how-to-spin-up-a-simple-flask-app-using-nginx-in-15-minutes-or-less/

- Set dev environment to use the same redirects
  - https://gist.github.com/Larivact/1ee3bad0e53b2e2c4e40

- Create login for apps
  - https://hackersandslackers.app/flask-login-user-authentication/

- Create script to copy files in deploy to directories
  - THIS should eventually be CI/CD -> Github Actions
  - deploy.sh
  - Use the examples from Hackers and Slackers
    - https://github.com/hackersandslackers/flask-session-tutorial

- SSL for nginx
  - https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04
    - Step 6 - Securing the Application

- CI/CD
  - Github Actions

- Tests
  - Pytest
    - So scurred

- To-Do list API with FastAPI
  - https://fastapi.tiangolo.com/tutorial/

- TO DO LIST:
  - [X] When making a new task, give it a priority 1-100.  Give the scale as < 10 urgent and 10-20 important, etc. until 90-100 long term
  - [X] Tasks get sorted by priority, with adding timestamp being the deciding factor for ties in priority, so that older tasks get done first.
  - [ ] For every week that a task is on the list, it should get bumped an extra 5 points so that it's priority goes up and eventually it makes it to the top. 5 points X 20 == 100 so it would be top priority in 20 weeks ~ < 6 months.  Perfect.
  - [ ] For each task on the today list, THERE CAN ONLY BE 5 AT A TIME, it goes by priority.  Only tasks with priority 0 get put on the list as extra and put to the top.  Priority 0 is Emergency and should be used very sparingly, to avoid daily bloat and slowdown.
  - [ ] Description for each task can be markdown, and it will format it.
  - [ ] Each task has a button that says `Tomorrow` so it can be moved to the next day if there are blockers.
  - [X] Tasks are best broken into small units of work and then arranged according to order so that they can be accomplished in order on the list.
  - [X] Only 5 tasks are given each day, these are tasks outside of the daily habits.
  - [X] Check marks should auto-save, no need to hit save or submit on each one, just the clicking of the button should submit the form





- NEW APP (Very low priority)
  - Interview Star Questions
    - Have it talk to the command line version
    - Update Command line Version
    - Maybe use rich?
      - https://github.com/Textualize/rich