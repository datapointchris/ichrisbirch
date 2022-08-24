# Project Structure



# First time


### FastAPI Crud Endpoints
You have to specify keyword arguments after `db` because of the function signature with `*`
Order matters with endpoints, dynamic routes `route/endpoint/{id}` are last


# Testing
In order to run pytest, you have to set `ENVIRONMENT=development` so that the config
can pick it up and set the correct variables.
Note: Config is not actually setting anything in tests, but the config is called in some of the files that are imported and it will error if not set.

