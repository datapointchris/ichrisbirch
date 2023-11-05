# Developer Setup

- [1. Programs to install](#1-programs-to-install)
- [2. Set up git-secret](#2-set-up-git-secret)
- [3. Setup the project](#3-setup-the-project)
- [4. Run the project](#4-run-the-project)
- [5. Connecting to the Running Project](#5-connecting-to-the-running-project)
  - [5.1. App](#51-app)
  - [5.2. API](#52-api)
- [6. Links and Notes](#6-links-and-notes)

## 1. Programs to install

poetry
git-secret
Docker Desktop

## 2. Set up git-secret

## 3. Setup the project

```bash
git clone https://github.com/datapointchris/ichrisbirch.git

cd ichrisbirch/

git secret reveal

poetry install

source .venv/bin/activate

export ENVIRONMENT=development

pre-commit install

# Make sure Docker is running

pytest
```

## 4. Run the project

!!! todo "TODO"

  This doesn't work!  I need to figure out another way to run it locally.
  Right now it is relying on using local NGINX and Supervisor.

```bash
# App and API are separate applications.
# App is a flask app that runs the frontend
# API is FastAPI running the API backend that the frontend connects to

# Run these in separate shells for log separation
# poetry run python ichrisbirch/runapidev.py
# poetry run python ichrisbirch/runappdev.py

```

## 5. Connecting to the Running Project

### 5.1. App

<http://127.0.0.1:6000>

### 5.2. API

<http://127.0.0.1:6200>

## 6. Links and Notes

[GitHub - github/scripts-to-rule-them-all: Set of boilerplate scripts describing the normalized script pattern that GitHub uses in its projects.](https://github.com/github/scripts-to-rule-them-all)
