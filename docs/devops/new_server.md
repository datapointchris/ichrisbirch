# Setup a New Server

## Installs

```bash
# Update
sudo apt update && sudo apt upgrade -y

# Install apt required
sudo apt install zsh tmux tldr supervisor nginx neofetch pipx curl git git-secret build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl git libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev -y
pipx ensurepath

# Install pyenv
curl https://pyenv.run | bash

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

exec $SHELL

# Install python
pyenv install 3.12

# Install poetry
pipx install poetry

##### AT THIS POINT THE AMI SHOULD BE MADE #####

# Clone project
sudo chown ubuntu /var/www
git clone https://github.com/datapointchris/ichrisbirch /var/www/ichrisbirch
git secret reveal

# Install project
poetry config virtualenvs.in-project true
poetry install

# Make log files for project
./scripts/make_log_files.sh

# Set up nginx and supervisor
cd deploy
./deploy-nginx.sh
sudo rm /etc/nginx/sites-enabled/default

./deploy-supervisor.sh
```

Change the elastic IP to point to the new server (if only using one server and not load balancer).
