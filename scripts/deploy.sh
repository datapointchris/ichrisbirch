#------------------------------ COLOR AND FORMATTING ------------------------------#
black=$(tput setaf 0)
red=$(tput setaf 1)
green=$(tput setaf 2)
yellow=$(tput setaf 3)
blue=$(tput setaf 4)
magenta=$(tput setaf 5)
cyan=$(tput setaf 6)
white=$(tput setaf 7)
bold=$(tput bold)
underline=$(tput smul)
normal=$(tput sgr0)
colors=($black $red $green $yellow $blue $magenta $cyan $white)

function get_color() {
    case $1 in
        'black') map_color=${colors[0]} ;;
        'red') map_color=${colors[1]} ;;
        'green') map_color=${colors[2]} ;;
        'yellow') map_color=${colors[3]} ;;
        'blue') map_color=${colors[4]} ;;
        'magenta') map_color=${colors[5]} ;;
        'cyan') map_color=${colors[6]} ;;
        'white') map_color=${colors[7]} ;;
        *) map_color="" ;;
    esac
}

# Print Colored Lines
function echo_section_title() { 
	local color="$2"
    : "${color:=blue}" # default to blue if color not specified
	get_color "$color"
	echo "${underline}$map_color          $1          ${normal}"; 
	}
function echo_create() { echo "${yellow}Create:${normal} $1"; }
function echo_update() { echo "${green}Update:${normal} $1 ${green} --> ${normal} $2"; }
function echo_copy() { echo "${green}Copy:${normal} $1 ${green} --> ${normal} $2"; }
function echo_symlink() { echo "${magenta}Symlink:${normal} $1 ${magenta} --> ${normal} $2"; }

function echo_separator() {
    local sep=""
    local terminal_width=$(tput cols)
    for ((i = 0; i < terminal_width; i++)); do
        sep="$sep:"
    done
    echo "$sep"
}

function echo_colorchar() {
    local sep=""
    local terminal_width=$(tput cols)
    local color="$2"
    local num_chars="$3"
    : "${color:=normal}" # default to normal if color not specified
    : "${num_chars:=terminal_width}" # default to terminal width if num_chars not specified
    for ((i = 0; i < $num_chars; i++)); do
        sep="$sep$1"
    done
    get_color "$color" # get_color sets map_color
    sep="$map_color$sep${normal}"
    echo "$sep"
}

function echo_randcolorchar() {
    local sep=""
    local terminal_width=$(tput cols)
    local num_chars="$2"
    : "${num_chars:=terminal_width}"
    for ((i = 0; i < $num_chars; i++)); do
        rand_color_idx=$(($RANDOM % ${#colors[@]}))
        rand_color=${colors[$rand_color_idx]}
        sep="$sep$rand_color$1"
    done
    sep="$sep${normal}"
    echo "$sep"
}

function echo_center_text() {
    local columns="$(tput cols)"
    local str_length=`echo "$1" | sed -r 's/\x1b\[[0-9;]*m//g' | wc -c`
    local filler_length="$(( (columns - str_length) / 2 - 4 ))"
    local spaces=""
    for ((i = 0; i < filler_length; i++)); do
        spaces="$spaces "
    done
    echo "$spaces$1$spaces"
}

function echo_error() {
    echo "${bold}${red}ERROR: ${normal}${red}$1${normal}"
}


################################################################################
ABOUT="
$(echo_section_title "*-*-*  Deploy Supervisor and NGINX Config Files  *-*-*")

  ${green}USAGE${normal}
  Run as ./deploy.sh {environment}

  ${green}EXAMPLE${normal}
  ./deploy.sh dev
 
  ${green}HELP${normal}
  ./deploy.sh --help

  ${green}ACTIONS${normal}
  Copy: NGINX config file
  Copy: NGINX sites-available config file(s)
  Symlink: NGINX sites-enabled config file(s)
  
  Copy: Supervisor config file
  Copy: Supervisor api config file
  Copy: Supervisor app config file
  Create: Supervisor api log files
  Create: Supervisor app log files
 
  ${green}DEPENDENCIES${normal}
  nginx
  supervisor
"""

################################################################################
# Fail script on command fail
set -e





#------------------------------ SCRIPT HELPER FUNCTIONS ------------------------------#
function yell() {
    echo "$0: $*" >&2
    }

function die() {
    yell "$*"; exit 1
    }

function try() {
    "$@" || die "cannot $*"
    }

function help() {
	if [ -n "$1" ]; then
		command echo "$ABOUT" | grep "$1"
	else
		command echo "$ABOUT"
	fi
}

function usage() { 
    echo "${bold}${green}Usage:${normal}"
    echo "$0 [dev, test, prod]"
    echo "${green}Example:${normal}"
    echo "$0 dev"
    1>&2;
    }



#------------------------------ SCRIPT PROCESSING ------------------------------#
# Get project name from current dir
PROJECT=$(basename $PWD)

# -- Check for arguments -- #
# The pattern:
# 1. If no arguments: show usage, no error
# 2. Check for particular flags
# 3. Assign variables
# NOTE: No exit codes inside the functions so they can be more generic

if [[ -z "$1" ]]; then
    usage
    exit 0;

elif [[ "$1" = "--help" ]]; then
    shift
    help "$@"
    exit 0;
fi

# Get environment flag
ENVIRONMENT=$1
case $ENVIRONMENT in
    dev) OS_PREFIX="/usr/local" ;;
    test) OS_PREFIX="" ;;
    prod) OS_PREFIX="" ;;
    *) echo_error "Unsupported environment flag: $ENVIRONMENT"
       usage 
       exit 1 ;;
esac
ENV_CONFIG_DIR="deploy/$ENVIRONMENT"


#------------------------------ SCRIPT TITLE ------------------------------#
echo ""
echo_colorchar "-" "black"
echo_center_text "$(echo_colorchar "/" "green" 10)  \t${blue}${underline}Deploying ${green}$PROJECT${blue} project in ${green}$ENVIRONMENT ${blue}environment${normal}\t    $(echo_colorchar "\\\\" "green" 20)"
echo_colorchar "=" "black"
echo ""


#------------------------------ NGINX ------------------------------#
echo_section_title "NGINX"
NGINX_DIR="$OS_PREFIX/etc/nginx"
SITES_AVAILABLE="$NGINX_DIR/sites-available"
SITES_ENABLED="$NGINX_DIR/sites-enabled"

sudo mkdir -p $SITES_AVAILABLE
sudo mkdir -p $SITES_ENABLED
echo_create "$NGINX_DIR"
echo_create "$SITES_AVAILABLE"
echo_create "$SITES_ENABLED"

sudo cp $ENV_CONFIG_DIR/nginx.conf $NGINX_DIR/nginx.conf
sudo cp $ENV_CONFIG_DIR/nginx-api.conf $SITES_AVAILABLE/$PROJECT-api.conf
sudo cp $ENV_CONFIG_DIR/nginx-app.conf $SITES_AVAILABLE/$PROJECT-app.conf
echo_copy "$ENV_CONFIG_DIR/nginx.conf" "$NGINX_DIR/nginx.conf"
echo_copy "$ENV_CONFIG_DIR/nginx-api.conf" "$SITES_AVAILABLE/$PROJECT-api.conf"
echo_copy "$ENV_CONFIG_DIR/nginx-app.conf" "$SITES_AVAILABLE/$PROJECT-app.conf"

sudo ln -sf $SITES_AVAILABLE/$PROJECT-api.conf $SITES_ENABLED/$PROJECT-api.conf
sudo ln -sf $SITES_AVAILABLE/$PROJECT-app.conf $SITES_ENABLED/$PROJECT-app.conf
echo_symlink "$SITES_AVAILABLE/$PROJECT-api.conf" "$SITES_ENABLED/$PROJECT-api.conf"
echo_symlink "$SITES_AVAILABLE/$PROJECT-app.conf" "$SITES_ENABLED/$PROJECT-app.conf"
echo ""


#------------------------------ SUPERVISOR ------------------------------#
echo_section_title "SUPERVISOR"
BASE_DIR="$OS_PREFIX/etc"
SUPERVISOR_CONFIG_DIR="$BASE_DIR/supervisor.d"
SUPERVISOR_LOG_DIR="$OS_PREFIX/var/log/supervisor"
# Note: Make sure log direcitories match entries in `supervisord.conf`

# Directories
sudo mkdir -p $SUPERVISOR_CONFIG_DIR
sudo mkdir -p $SUPERVISOR_LOG_DIR
echo_create "$SUPERVISOR_CONFIG_DIR"
echo_create "$SUPERVISOR_LOG_DIR"

# Configuration
sudo cp $ENV_CONFIG_DIR/supervisord.conf $BASE_DIR/supervisord.conf
sudo cp $ENV_CONFIG_DIR/supervisor-app.conf $SUPERVISOR_CONFIG_DIR/$PROJECT-app.conf
sudo cp $ENV_CONFIG_DIR/supervisor-api.conf $SUPERVISOR_CONFIG_DIR/$PROJECT-api.conf
echo_copy "$ENV_CONFIG_DIR/supervisord.conf" "$BASE_DIR/supervisord.conf"
echo_copy "$ENV_CONFIG_DIR/supervisor-app.conf" "$SUPERVISOR_CONFIG_DIR/$PROJECT-app.conf"
echo_copy "$ENV_CONFIG_DIR/supervisor-api.conf" "$SUPERVISOR_CONFIG_DIR/$PROJECT-api.conf"

# Logs
sudo touch $SUPERVISOR_LOG_DIR/supervisord.log
sudo touch $SUPERVISOR_LOG_DIR/$PROJECT-api-out.log
sudo touch $SUPERVISOR_LOG_DIR/$PROJECT-api-error.log
sudo touch $SUPERVISOR_LOG_DIR/$PROJECT-app-out.log
sudo touch $SUPERVISOR_LOG_DIR/$PROJECT-app-error.log
echo_create "$SUPERVISOR_LOG_DIR/supervisord.log"
echo_create "$SUPERVISOR_LOG_DIR/$PROJECT-api-out.log"
echo_create "$SUPERVISOR_LOG_DIR/$PROJECT-api-error.log"
echo_create "$SUPERVISOR_LOG_DIR/$PROJECT-app-out.log"
echo_create "$SUPERVISOR_LOG_DIR/$PROJECT-app-error.log"
echo ""

# Set owner on MacOS in dev
if [[ $ENVIRONMENT = "dev" ]]; then
    echo_section_title "PERMISSIONS"
    sudo chown -R $USER $NGINX_DIR
    sudo chown -R $USER $BASE_DIR/supervisord.conf
    sudo chown -R $USER $SUPERVISOR_CONFIG_DIR
    sudo chown -R $USER $SUPERVISOR_LOG_DIR
    echo "Change owner of ${green}$NGINX_DIR/${normal} to user: ${blue}$USER${normal}"
    echo "Change owner of ${green}$BASE_DIR/supervisord.conf${normal} to user: ${blue}$USER${normal}"
    echo "Change owner of ${green}$SUPERVISOR_CONFIG_DIR/${normal} to user: ${blue}$USER${normal}"
    echo "Change owner of ${green}$SUPERVISOR_LOG_DIR/${normal} to user: ${blue}$USER${normal}"
    echo ""
fi


#------------------------------ APACHE ------------------------------#
# Change permissions for www folder
# sudo chown -R $USER:www-data /var/www
# sudo find /var/www -type d -exec chmod 2750 {} \+
# sudo find /var/www -type f -exec chmod 640 {} \+


#------------------------------ SUCCESS ------------------------------#
echo_center_text "${black}=====-----=====-----===== ${green} All files copied ${black} =====-----=====-----=====${normal}"
echo ""
echo "${bold}${blue}Remember to restart nginx and supervisor${normal}"
echo "sudo supervisorctl reload"
echo "sudo nginx -s reload"
echo ""