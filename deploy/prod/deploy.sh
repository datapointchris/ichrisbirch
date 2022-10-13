# Project vars
PROJECT_NAME=euphoria
SUPERVISOR_LOG_DIR=/var/log/supervisor

# Copy nginx file to sites-available
sudo cp nginx-app.conf /etc/nginx/sites-available/$PROJECT_NAME-app.conf
sudo cp nginx-api.conf /etc/nginx/sites-available/$PROJECT_NAME-api.conf

# Symlink the nginx file to sites-enabled
sudo ln -s /etc/nginx/sites-available/$PROJECT_NAME-app.conf /etc/nginx/sites-enabled/$PROJECT_NAME-app.conf
sudo ln -s /etc/nginx/sites-available/$PROJECT_NAME-api.conf /etc/nginx/sites-enabled/$PROJECT_NAME-api.conf

# Copy supervisor config file
sudo cp supervisor.conf /etc/supervisor/conf.d/$PROJECT_NAME.conf

# Create log directories as specified in `supervisor.conf`
sudo mkdir -p SUPERVISOR_LOG_DIR/$PROJECT_NAME
sudo touch SUPERVISOR_LOG_DIR/$PROJECT_NAME-app-out.log
sudo touch SUPERVISOR_LOG_DIR/$PROJECT_NAME-app-error.log
sudo touch SUPERVISOR_LOG_DIR/$PROJECT_NAME-api-out.log
sudo touch SUPERVISOR_LOG_DIR/$PROJECT_NAME-api-error.log

## Maybe I don't need to do this if not using apache
# Change permissions for www folder
# sudo chown -R $USER:www-data /var/www
# sudo find /var/www -type d -exec chmod 2750 {} \+
# sudo find /var/www -type f -exec chmod 640 {} \+

# Restart supervisor
sudo supervisorctl reload

# Restart Nginx
sudo nginx -s reload
