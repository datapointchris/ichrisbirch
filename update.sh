# Test the updated server configs
git pull
cd deplot/prod
sudo deploy.sh

sudo nginx -s reload
