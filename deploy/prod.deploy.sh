# Project name
PROJECT_NAME=euphoria

# Copy nginx file to sites-available
sudo cp prod.nginx.conf /etc/nginx/sites-available/$PROJECT_NAME.conf

# Symlink the nginx file to sites-enabled
sudo ln -s /etc/nginx/sites-available/$PROJECT_NAME.conf /etc/nginx/sites-enabled/$PROJECT_NAME.conf

# Copy supervisor config file
sudo cp prod.supervisor.conf /etc/supervisor/conf.d/$PROJECT_NAME.conf

# Create log directories as specified in `supervisor.conf`
sudo mkdir -p /var/log/$PROJECT_NAME
sudo touch /var/log/$PROJECT_NAME/app/out.log
sudo touch /var/log/$PROJECT_NAME/app/err.log
sudo touch /var/log/$PROJECT_NAME/api/out.log
sudo touch /var/log/$PROJECT_NAME/api/err.log

# Change permissions for www folder
sudo chown -R $USER:www-data /var/www
sudo find /var/www -type d -exec chmod 2750 {} \+
sudo find /var/www -type f -exec chmod 640 {} \+

# Restart supervisor
sudo supervisorctl reload

# Restart Nginx
sudo nginx -s reload
