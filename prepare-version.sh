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
    : "${color:=normal}"
    : "${num_chars:=terminal_width}"
    for ((i = 0; i < $num_chars; i++)); do
        sep="$sep$1"
    done
    get_color "$color"
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
$(echo_section_title "*-*-*  Prepare a Release Version  *-*-*")

  ${green}USAGE${normal}
  Run as ./prepare-version.sh {version} 'Version Description'
  The project name is the working directory
  MUST leave off the v in version:
  YES => 0.5.0
  NO => v0.5.0

  ${green}EXAMPLE${normal}
  ./prepare-version.sh 0.5.2 'Add API Endpoint'

  ${green}INTERACTIVE MODE${normal}
  ./prepare-version.sh --interactive
 
  ${green}HELP${normal}
  ./prepare-version.sh --help
 
  ${green}ACTIONS${normal}
  1. Create directory '{project}/stats/{version}'
  2. Update 'pyproject.toml'
  3. Update '{project}/__init__.py'
  4. Run pytest and create coverage report
  5. Run tokei and create lines of code report
  6. Run wily and create code complexity report
 
  ${green}DEPENDENCIES${normal}
  tokei
  wily
"

################################################################################
# Fail script on command fail
set -e

# TODO: [2022/10/27] - Add the release procedure with git
# Should start from develop, create a release branch, merge with master
# Push master and git tags
# Merge master into develop




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
    echo "${green}Command Line with Arguments:${normal}"
    echo "./prepare-version.sh 0.5.2 'Add API Endpoint'"
    echo "${green}Interactive:${normal}"
    echo "./prepare-version.sh interactive"
    1>&2;
    }

function interactive() {
    echo "Release version:"
    read SEMVER
    VERSION="v$SEMVER"
    echo "Version description: "
    read VERSION_DESCRIPTION
}


#------------------------------ SCRIPT PROCESSING ------------------------------#
# Get project name from current dir
PROJECT=$(basename $PWD)
CURRENT_VERSION=$(grep --only-matching "\d.\d.\d" "$PROJECT/__init__.py")

# -- Check for arguments -- #
# The pattern:
# 1. If no arguments: show usage, no error
# 2. Check for particular flags
# 3. Check all required arguments supplied
# 4. Looks good, assign variables
# NOTE: No exit codes inside the functions so they can be more generic

if [[ -z "$1" ]]; then
    usage
    exit 0;

elif [[ "$1" = "--help" ]]; then
    shift
    help "$@"
    exit 0;

elif [[ "$1" = "--interactive" ]]; then
    interactive 

elif [[ -z "$1" ]] || [[ -z "$2" ]]; then
    echo_error "Incorrect arguments"
    usage
    exit 1;
else
    SEMVER=$1
    # SEMVER is format: 1.1.1 -> useful for string replacement in files
    VERSION="v$1"
    # VERISON is format: v1.1.1 -> useful for folder and file names
    VERSION_DESCRIPTION=$2
fi


#------------------------------ SCRIPT TITLE ------------------------------#
echo ""
echo_colorchar "-" "black"
echo_center_text "$(echo_colorchar "-" "blue" 5)  \t${blue}${underline}Preparing Release for $VERSION - $VERSION_DESCRIPTION${normal}\t    $(echo_colorchar "-" "blue" 5)"
echo_colorchar "=" "black"
echo ""


#------------------------------ VERSION DIRECTORY ------------------------------#
VERSION_DIR="$PROJECT/stats/$VERSION"
mkdir -p $VERSION_DIR
echo_create $VERSION_DIR


#------------------------------ COVERAGE REPORT ------------------------------#
cd $PROJECT/
coverage report -m > stats/$VERSION/coverage.txt
coverage json -o stats/$VERSION/coverage.json
echo_create "$VERSION_DIR/coverage.txt"
echo_create "$VERSION_DIR/coverage.json"


#------------------------------ TOKEI LINES OF CODE ------------------------------#
cd ../
tokei . --exclude .venv --exclude $PROJECT/backend/alembic/versions/ > $VERSION_DIR/lines_of_code.txt
echo_create "$VERSION_DIR/lines_of_code.txt"
tokei . --exclude .venv --exclude $PROJECT/backend/alembic/versions/ -o json > $VERSION_DIR/lines_of_code.json
echo_create "$VERSION_DIR/lines_of_code.json"


#------------------------------ WILY CODE COMPLEXITY ------------------------------#
# wily does not have json output at the moment
wily build .
wily diff . -r master > $VERSION_DIR/complexity.txt
echo_create "$VERSION_DIR/complexity.txt"


#------------------------------ UPDATE VERSIONS IN FILES ------------------------------#
poetry version $SEMVER
echo_update "pyproject.toml $CURRENT_VERSION" "$SEMVER"

echo "__version__ = '$SEMVER'" > $PROJECT/__init__.py
echo_update "$PROJECT/__init__.py $CURRENT_VERSION" "$SEMVER"


#------------------------------ SUCCESS ------------------------------#
echo ""
echo_center_text "${black}=====-----=====-----===== ${green} Successfully Created Release: $VERSION ${black} =====-----=====-----=====${normal}"
