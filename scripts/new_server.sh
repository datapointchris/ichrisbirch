#!/usr/bin/env bash

sudo apt update && sudo apt upgrade -y

# base installs
sudo apt install curl git git-secret -y

# NOTE: Install the postgresql-client version that matches the database, this is for pg_dump backups with the scheduler.
sudo apt install postgresql-client-16 unzip tmux tldr supervisor nginx neovim -y

# for building psycopg from source
sudo apt install python3-dev libpq-dev gcc -y

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Get public and private gpg keys from S3 for unlocking git-secret .env files
aws s3 cp s3://ichrisbirch-webserver-keys/ec2-public.key "$HOME/ec2-public.key"
aws s3 cp s3://ichrisbirch-webserver-keys/ec2-private.key "$HOME/ec2-private.key"

# Import the keys
gpg --import "$HOME/ec2-public.key"
gpg --allow-secret-key-import --import "$HOME/ec2-private.key"

# Delete the key files
rm "$HOME/ec2-public.key"
rm "$HOME/ec2-private.key"

# Install poetry
export POETRY_HOME=/etc/poetry
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$POETRY_HOME/bin:$PATH"
echo "export PATH=\"$POETRY_HOME/bin:$PATH\"" >> ~/.bashrc
poetry config virtualenvs.in-project true

git clone https://github.com/datapointchris/ichrisbirch /var/www/ichrisbirch

# Set permissions - ubuntu must own in order to poetry install and git secret reveal
sudo chown -R ubuntu /var/www

cd /var/www/ichrisbirch || return

# Install project
poetry install --without dev,cicd

# Unlock secret files
git secret reveal

# Make log files for project
./scripts/make_log_files.sh

# Set up nginx and supervisor
sudo rm /etc/nginx/sites-enabled/default

cd deploy || return

./deploy-nginx.sh

./deploy-supervisor.sh

sudo reboot
