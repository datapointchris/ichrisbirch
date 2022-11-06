# Deploy the project in professional fashion




## Dev
**`Dev`** assumes MacOS and homebrew installations
**`HOST:`** 0.0.0.0
**`APP PORT:`** 4000
**`API PORT:`** 4200



## Test
**`Test`** assumes Ubuntu and apt installations
**`HOST:`** 0.0.0.0
**`APP PORT:`** 4000
**`API PORT:`** 4200



## Prod
**`Prod`** assumes Ubuntu and apt installations
**`HOST:`** ichrisbirch.com
**`APP PORT:`** 8000
**`API PORT:`** 8200
Number of workers is 1 for each in supervisor conf files because of small EC2 instance

TODO: This is not right
Probably encrypt and decrypt them all
1. Decrypt or copy environment file
 `scp -i ~/.ssh/apps.pem .prod.env ubuntu@$EUPHORIA_IP:/var/www/euphoria/`

TODO: This does not work on Ubuntu
2. Install the project
`poetry install --without dev`
Note: if there is pyscopg2 error about gcc:
`sudo apt install libpq-dev`

3. Run `deploy.sh`

4. Restart supervisor and nginx




# New Server

## Check for updates 
sudo apt update
sudo apt upgrade -y

## Installs
 TODO: [2022/10/31] - Put zsh and dotfiles on here
sudo apt install -y tmux tmuxinator tree htop sysstat procps tldr libpq-dev libffi-dev python3-cachecontrol python3.10 python3-poetry nginx supervisor

## Clone Project
sudo git clone https://github.com/datapointchris/euphoria.git /var/www/

## Secure copy the environment file (from local)
scp -i ~/.ssh/apps.pem ~/github/projects/euphoria/deploy/prod/.prod.env ubuntu@$EUPHORIA_IP:/var/www/euphoria/deploy/prod/.prod.env

## Install project
poetry config virtualenvs.in-project true
poetry install --without dev

## Run deploy script to copy supervisor and nginx config files
sudo chmod +x /var/www/euphoria/deploy/prod/deploy.sh
sudo /var/www/euphoria/deploy/prod/deploy.sh

## Restart nginx and supervisor
sudo supervisorctl reload
sudo nginx -s reload

## ** Locally ** Make sure of no errors
tmuxinator euphoria-prod-monitoring
