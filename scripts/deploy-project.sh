#!/usr/bin/env bash

git pull

poetry install

sudo supervisorctl reload
