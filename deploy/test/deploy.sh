# Commandline Colors
bold=$(tput bold)
blue=$(tput setaf 4)
green=$(tput setaf 2)
red=$(tput setaf 1)
normal=$(tput sgr0)

# PROJECT VARS
PROJECT_NAME=euphoria
echo "${bold}${blue}----- Deploying $PROJECT_NAME -----${normal}"

# NGINX
SITES_AVAILABLE="/etc/nginx/sites-available"
sudo cp nginx-app.conf $SITES_AVAILABLE/$PROJECT_NAME-app.conf
sudo cp nginx-api.conf $SITES_AVAILABLE/$PROJECT_NAME-api.conf
echo "Copied NGINX project config files to $SITES_AVAILABLE/"

SITES_ENABLED="/etc/nginx/sites-enabled"
sudo ln -sf $SITES_AVAILABLE/$PROJECT_NAME-app.conf $SITES_ENABLED/$PROJECT_NAME-app.conf
sudo ln -sf $SITES_AVAILABLE/$PROJECT_NAME-api.conf $SITES_ENABLED/$PROJECT_NAME-api.conf
echo "Symlinked NGINX project config files to $SITES_ENABLED/"

# SUPERVISOR
SUPERVISOR_DIR="/etc/supervisor"
sudo cp supervisord.conf $SUPERVISOR_DIR/supervisord.conf
echo "Copied supervisord config file to $SUPERVISOR_DIR/"

# Copy project config files
sudo cp supervisor-app.conf $SUPERVISOR_DIR/conf.d/$PROJECT_NAME-app.conf
sudo cp supervisor-api.conf $SUPERVISOR_DIR/conf.d/$PROJECT_NAME-api.conf
echo "Copied supervisor project config files to $SUPERVISOR_DIR/conf.d/"

# Note: Make sure log direcitories match entries in `supervisord.conf`
SUPERVISOR_LOG_DIR=/var/log/supervisor
sudo mkdir -p $SUPERVISOR_LOG_DIR/$PROJECT_NAME
sudo touch $SUPERVISOR_LOG_DIR/$PROJECT_NAME-app-out.log
sudo touch $SUPERVISOR_LOG_DIR/$PROJECT_NAME-app-error.log
sudo touch $SUPERVISOR_LOG_DIR/$PROJECT_NAME-api-out.log
sudo touch $SUPERVISOR_LOG_DIR/$PROJECT_NAME-api-error.log
echo "Created supervisor log files in $SUPERVISOR_LOG_DIR/$PROJECT_NAME/"

## APACHE
# Change permissions for www folder
# sudo chown -R $USER:www-data /var/www
# sudo find /var/www -type d -exec chmod 2750 {} \+
# sudo find /var/www -type f -exec chmod 640 {} \+

echo "${bold}${green}----- All files copied -----${normal}\n"
echo "${bold}${blue}Remember to restart NGINX and supervisor${normal}"
echo "sudo supervisorctl reload"
echo "sudo nginx -s reload"
echo ""