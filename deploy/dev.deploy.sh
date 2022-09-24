# Project name
PROJECT_NAME=euphoria

# Create servers directory
mkdir -p /usr/local/etc/nginx/servers

# Link nginx file to sites-available
ln -s dev.nginx.conf /usr/local/etc/nginx/servers/$PROJECT_NAME.conf

# Create supervisor conf directory
mkdir -p /usr/local/etc/supervisor.d/

# Link supervisor config file
ln -s dev.supervisor.conf /usr/local/etc/supervisor.d/$PROJECT_NAME.conf

# Create log directories as specified in `supervisor.conf`
sudo mkdir -p /usr/local/var/log/supervisor/$PROJECT_NAME
sudo touch /usr/local/var/log/$PROJECT_NAME/app/out.log
sudo touch /usr/local/var/log/$PROJECT_NAME/app/error.log
sudo touch /usr/local/var/log/$PROJECT_NAME/api/out.log
sudo touch /usr/local/var/log/$PROJECT_NAME/api/error.log

# Restart supervisor
sudo supervisorctl reload

# Restart Nginx
sudo nginx -s reload
