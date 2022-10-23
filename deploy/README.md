# Deploy the project in professional fashion

Note: If you are getting supervisor.sock no such file, make sure directories and files for logs are created.

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

1. Decrypt or Copy `.prod.env`

2. Install the project
`poetry install`
Note: if there is pyscopg2 error about gcc:
`sudo apt install libpq-dev`

3. Run `deploy.sh`

4. Restart supervisor and nginx




# New Server

## Check for updates 
sudo apt update
sudo apt upgrade -y

## Installs
sudo apt install -y tmux htop python3.10 python3-poetry nginx supervisor

## Clone Project
sudo git clone https://github.com/datapointchris/euphoria.git /var/www/

## Run deploy script to copy supervisor and nginx config files
sudo chmod +x /var/www/euphoria/deploy/prod/deploy.sh
sudo /var/www/euphoria/deploy/prod/deploy.sh

## Restart nginx and supervisor
sudo supervisorctl reload
sudo nginx -s reload

## ** Locally ** Make sure of no errors
tmuxinator euphoria-prod-monitoring
