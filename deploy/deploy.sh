# shebang

# PREREQUESITES
# Change name in `supervisor.conf` to PROJECT_NAME

# Project name
$PROJECT_NAME=euphoria

# Copy nginx file to sites-available
sudo cp nginx.conf /etc/nginx/sites-available/$PROJECT_NAME.conf

# Symlink the nginx file to sites-enabled
sudo ln -s /etc/nginx/sites-available/$PROJECT_NAME.conf /etc/nginx/sites-enabled/$PROJECT_NAME.conf

# Copy supervisor config file with .conf
sudo cp supervisor.conf /etc/supervisor/conf.d/$PROJECT_NAME.conf

# Create log directories as specified in `supervisor.conf`
sudo mkdir /var/log/$PROJECT_NAME
sudo touch /var/log/$PROJECT_NAME/out.log
sudo touch /var/log/$PROJECT_NAME/err.log

# Change permissions for www folder
sudo chown -R $USER:www-data /var/www
sudo find /var/www -type d -exec chmod 2750 {} \+
sudo find /var/www -type f -exec chmod 640 {} \+

# Restart supervisor
sudo supervisorctl reload

# Restart Nginx
sudo nginx -s reload
