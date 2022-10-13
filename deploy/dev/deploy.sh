# Project vars
PROJECT_NAME=euphoria
SUPERVISOR_LOG_DIR=/usr/local/var/log/supervisor

# Create servers directory
mkdir -p /usr/local/etc/nginx/servers

# Link nginx file to sites-available (servers cuz brew)
ln -s nginx.conf /usr/local/etc/nginx/servers/$PROJECT_NAME.conf

# Create supervisor conf directory
mkdir -p /usr/local/etc/supervisor.d/
# Link supervisor config file
ln -s supervisor.conf /usr/local/etc/supervisor.d/supervisor.conf

# Link euphoria app config file
ln -s supervisor-app.conf /usr/local/etc/

# Link euphoria api config file
ln -s supervisor-api.conf /usr/local/etc/

# Create log directory for supervisor
sudo mkdir -p $SUPERVISOR_LOG_DIR/$PROJECT_NAME

sudo touch $SUPERVISOR_LOG_DIR/$PROJECT_NAME-app-out.log
sudo touch $SUPERVISOR_LOG_DIR/$PROJECT_NAME-app-error.log
sudo touch $SUPERVISOR_LOG_DIR/$PROJECT_NAME-api-out.log
sudo touch $SUPERVISOR_LOG_DIR/$PROJECT_NAME-api-error.log

# Restart supervisor
sudo supervisorctl reload

# Restart Nginx
sudo nginx -s reload
