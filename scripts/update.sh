# Test the updated server configs
git pull
cd deploy/prod
chmod +x deploy.sh
sudo ./deploy.sh

sudo nginx -s reload
sudo supervisorctl reload
