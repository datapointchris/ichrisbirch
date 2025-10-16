#!/usr/bin/env bash

set_global_vars() {
  UBUNTU_HOME=/home/ubuntu
  KEY_BUCKET=ichrisbirch-webserver-keys
  PUBLIC_KEY=ec2-public.key
  PRIVATE_KEY=ec2-private.key
  AWS_CLI_ZIP="https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip"
  TMUX_CONFIG_GIST="https://gist.github.com/2054319eca6c91523355590fed6135d6.git"
  TMUX_CONFIG_DIR="$UBUNTU_HOME/.config/tmux"
}

update_machine() {
  apt update && apt upgrade -y
}

base_installs() {
  # NOTE: Install the postgresql-client version that matches the database
  # this is for pg_dump backups with the scheduler.
  apt install curl git git-secret postgresql-client-16 unzip make -y
  apt install tmux tldr tree supervisor nginx neovim -y
}

installs_for_building_psycopg2_from_source() {
  apt install python3-dev libpq-dev gcc -y
}

install_aws_cli() {
  curl "$AWS_CLI_ZIP" -o "$UBUNTU_HOME/awscliv2.zip"
  cd $UBUNTU_HOME || return
  unzip awscliv2.zip
  ./aws/install >/dev/null 2>&1
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

setup_tmux() {
  mkdir -p "$TMUX_CONFIG_DIR"
  curl "$TMUX_CONFIG_GIST" -o "$TMUX_CONFIG_DIR"
  rm -rf "$TMUX_CONFIG_DIR/.git"
}

install_uv() {
  # Install UV for all users
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Add UV to PATH for ubuntu user
  # shellcheck disable=SC2016
  echo 'export PATH="$HOME/.cargo/bin:$PATH"' >>"$UBUNTU_HOME/.bashrc"
  # shellcheck disable=SC1091
  source "$UBUNTU_HOME/.bashrc"
}

clone_repo() {
  git clone https://github.com/datapointchris/ichrisbirch /var/www/ichrisbirch
}

install_project() {
  cd /var/www/ichrisbirch && ~/.cargo/bin/uv sync --frozen --no-dev
}

unlock_secret_files() {
  cd /var/www/ichrisbirch && git secret reveal -f
}

make_log_files() {
  /var/www/ichrisbirch/scripts/make_log_files.sh
}

install_certbot() {
  snap install --classic certbot
  ln -s /snap/bin/certbot /usr/bin/certbot
}

install_ssl_certificate_for_nginx() {
  # note: no need for docs.ichrisbirch because Github Pages handles in the Pages > Custom domain section
  certbot certonly --cert-name ichrisbirch.com --nginx \
    --non-interactive --agree-tos --no-eff-email --email ichrisbirch@gmail.com \
    --domains ichrisbirch.com,www.ichrisbirch.com,api.ichrisbirch.com,chat.ichrisbirch.com
}

setup_nginx() {
  rm /etc/nginx/sites-enabled/default
  # Must cd here because the deploy script has relative paths
  cd /var/www/ichrisbirch/deploy && ./deploy-nginx.sh
}

setup_redis() {
  wget https://download.redis.io/redis-stable.tar.gz
  tar -xzvf redis-stable.tar.gz
  cd redis-stable && make
  make install

  cd ../
  rm -rf redis-stable
  rm redis-stable.tar.gz

  mkdir /etc/redis
  mkdir /var/redis

  # Must cd here because the deploy script has relative paths
  cd /var/www/ichrisbirch/deploy && ENVIRONMENT=production sudo ./deploy-redis.sh

  update-rc.d redis defaults
}

setup_supervisor() {
  # Must cd here because the deploy script has relative paths
  cd /var/www/ichrisbirch/deploy && ./deploy-supervisor.sh
}

set_permissions() {
  # Set permissions - ubuntu must own the directory for subsequent UV install and git secret reveal
  # Since startup script runs as root, change permissions at the end
  chown -R ubuntu /var/www
  chown redis:redis /var/lib/redis
  chmod 770 /var/lib/redis
}

main() {
  set_global_vars
  update_machine
  base_installs
  installs_for_building_psycopg2_from_source
  install_aws_cli
  import_gpg_keys
  setup_tmux
  install_uv
  clone_repo
  install_project
  unlock_secret_files
  make_log_files
  install_certbot
  # This may be a manual step of copying certs from old to new
  # install_ssl_certificate_for_nginx
  setup_nginx
  setup_redis
  setup_supervisor
  set_permissions
  reboot
}

main || exit 1
