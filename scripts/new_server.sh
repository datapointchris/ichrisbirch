#!/usr/bin/env bash

set_global_vars() {
    UBUNTU_HOME=/home/ubuntu
    KEY_BUCKET=ichrisbirch-webserver-keys
    PUBLIC_KEY=ec2-public.key
    PRIVATE_KEY=ec2-private.key
    POETRY_HOME=/etc/poetry
    POETRY_BIN_DIR=$POETRY_HOME/bin
    POETRY_EXE=$POETRY_BIN_DIR/poetry
}

update_machine() {
    apt update && apt upgrade -y
}

base_installs() {
    # NOTE: Install the postgresql-client version that matches the database
    # this is for pg_dump backups with the scheduler.
    apt install curl git git-secret postgresql-client-16 unzip tmux tldr tree supervisor nginx neovim -y
}

installs_for_building_psycopg2_from_source() {
    apt install python3-dev libpq-dev gcc -y
}

install_aws_cli() {
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "$UBUNTU_HOME/awscliv2.zip"
    cd $UBUNTU_HOME || return
    unzip awscliv2.zip
    ./aws/install > /dev/null 2>&1
}

import_gpg_keys() {
    # Get public and private gpg keys from S3 for unlocking git-secret .env files
    aws s3 cp "s3://$KEY_BUCKET/$PUBLIC_KEY" "$UBUNTU_HOME/$PUBLIC_KEY"
    aws s3 cp "s3://$KEY_BUCKET/$PRIVATE_KEY" "$UBUNTU_HOME/$PRIVATE_KEY"

    gpg --import "$UBUNTU_HOME/$PUBLIC_KEY"
    gpg --import "$UBUNTU_HOME/$PRIVATE_KEY"

    sudo -u ubuntu gpg --import "$UBUNTU_HOME/$PUBLIC_KEY"
    sudo -u ubuntu gpg --import "$UBUNTU_HOME/$PRIVATE_KEY"

    rm "$UBUNTU_HOME/$PUBLIC_KEY"
    rm "$UBUNTU_HOME/$PRIVATE_KEY"
}

install_poetry() {
    curl -sSL https://install.python-poetry.org | POETRY_HOME="$POETRY_HOME" python3 -
    # Add poetry to PATH for ubuntu since this script runs as root on startup
    echo "export PATH=\"$POETRY_BIN_DIR:$PATH\"" >> "$UBUNTU_HOME/.bashrc"
    $POETRY_EXE config virtualenvs.in-project true && echo "Set poetry to create virtualenvs in project directory"
    sudo -u ubuntu $POETRY_EXE config virtualenvs.in-project true && echo "Set poetry to create virtualenvs in project directory for ubuntu"
}

clone_repo() {
    git clone https://github.com/datapointchris/ichrisbirch /var/www/ichrisbirch
}

install_project() {
    cd /var/www/ichrisbirch && $POETRY_EXE install --without dev,cicd
}

unlock_secret_files() {
    cd /var/www/ichrisbirch && git secret reveal -f
}


make_log_files() {
    /var/www/ichrisbirch/scripts/make_log_files.sh
}

setup_nginx() {
    rm /etc/nginx/sites-enabled/default
    # Must cd here because the deploy script has relative paths
    cd /var/www/ichrisbirch/deploy && ./deploy-nginx.sh
}

setup_supervisor() {
    # Must cd here because the deploy script has relative paths
    cd /var/www/ichrisbirch/deploy && ./deploy-supervisor.sh
}

set_permissions() {
    # Set permissions - ubuntu must own the directory for subsequent poetry install and git secret reveal
    # Since startup script runs as root, change permissions at the end
    chown -R ubuntu /var/www
}

main() {
    set_global_vars
    update_machine
    base_installs
    installs_for_building_psycopg2_from_source
    install_aws_cli
    import_gpg_keys
    install_poetry
    clone_repo
    install_project
    unlock_secret_files
    make_log_files
    setup_nginx
    setup_supervisor
    set_permissions
    reboot
}

main || exit 1
