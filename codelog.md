## Friday, August 12, 2022
Goals:
- [X] Understand tasks again
- [X] Make decision on tasks function
- [X] Implement basic API functionality
- [ ] Create basic request tests for API

Notes:
- Finally getting back to coding on this.  I'm completely lost (of course) on what I was doing next except that I'm working on tasks.
- Not sure what I'm doing with the `tasks` API.  I wrote something similar to SQLAlchemy but it would be stupid and ridiculous to use that for anything more than basic.  Or would it?  Maybe I just need basic for these endpoints and I can see how it works across all of the different app endpoints.

** USING SQLAlchemy for ease of use across projects.

Ending Notes:
Tasks routes in `Euphoria` are done.
Tasks endpoints and db functions in API are done
Need to test out that it actually works with tasks
Create some tests for each endpoint
Create dummy sqlite test data and run integration tests


### Sunday, August 14, 2022: 
Goals:
- [ ] Make API Tests for Tasks
- [X] Get flask app working again
- [X] Make sure they connect properly
- [ ] Check for pg_cron on prod server
- [ ] Upload a new version of working tasks to prod

Notes:
- Right now the module renames have messed up the imports
- 

Ending Notes:
- API is working for endpoints
- The form is not tested
  - The endpoint for completing a task does not work


### Monday, August 15, 2022: 
Goals:
- [ ] API Endpoint tests
- [ ] 
- [ ] 
- [ ] 
Notes:
- 

Ending Notes:
- Cannot get completed and off and on other endpoints to work.
  - 422 Unprocessable entity - have not tracked it down yet
- Moving on to creating some automated requests tests for the API endpoints so I can see the failure pattern and find out what is causing the issue with the id not being integer type.
- Mother FUCKER it was the ordering of the endpoints!!!  Stupid dumbass cryptic messages and it was just some sill side note in the documentation!


### Tuesday, August 16, 2022: 
Goals:
- [X] Get all endpoints functioning
- [X] Get all of frontend functioning
- [ ] Make automated tests for all endpoints
- [ ] 
Notes:
- 

Ending Notes:
- Tasks frontend and backend are working.
  - Frontend is ugly and is not getting all the css correctly.
- All endpoints are working and tested
- I think the next order of business is to actually skip ahead and work on creating tests for these endpoints so that when I create the other endpoints and corresponding API calls I can easily test them without having to set up postman for all of that bullshit.


### Wednesday, August 17, 2022: 
Goals:
- [X] pytest 
- [X] endpoint tests
- [ ] 
- [ ] 
Notes:
- 

Ending Notes:
- All endpoint tests are working.  I need to next make it create a fake db in each of the tests so that I don't mess up my dev db each time I test.
- It should be in memory if possible and just put a few `things` in there.
  - Future of the db creation is being able to pass models and schemas into it to test that they are validating the information correctly on both ends.  


### Saturday, August 20, 2022: 
Goals:
- [ ] 
- [ ] 
- [ ] 
- [ ] 
Notes:
- 

Ending Notes:
- 

