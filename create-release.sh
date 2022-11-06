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
SCRIPT_NAME="$0"
ABOUT="
$(echo_section_title "*-*-*  Create a Release  *-*-*")

  ${green}USAGE${normal}
  Run as $SCRIPT_NAME {version} 'Version Description'
  The project name is the working directory
  MUST leave off the v in version:
  YES => 0.5.0
  NO => v0.5.0

  ${green}EXAMPLE${normal}
  $SCRIPT_NAME 0.5.2 'Add API Endpoint'

  ${green}INTERACTIVE MODE${normal}
  $SCRIPT_NAME --interactive
 
  ${green}HELP${normal}
  $SCRIPT_NAME --help
 
  ${green}ACTIONS${normal}
  ${yellow}NOTE:${normal} Make sure feature branch is merged in develop
  01. Create release branch from develop
  02. Create directory '{project}/stats/{version}'
  03. Update 'pyproject.toml'
  04. Update '{project}/__init__.py'
  05. Run pytest and create coverage report
  06. Run tokei and create lines of code report
  07. Run wily and create code complexity report
  08. Commit version stats to release branch
  09. Merge release branch into master
  10. Create a git tag on master using the version
  11. Merge release branch into develop
  12. Push all changes
 
  ${green}DEPENDENCIES${normal}
  tokei
  wily
"

################################################################################

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
    echo "$SCRIPT_NAME 0.5.2 'Add API Endpoint'"
    echo "${green}Interactive:${normal}"
    echo "$SCRIPT_NAME --interactive"
    echo "${green}Help:${normal}"
    echo "$SCRIPT_NAME --help"
    1>&2;
    }

function interactive() {
    echo "Release version:"
    read SEMVER
    VERSION="v$SEMVER"
    echo "Version description: "
    read VERSION_DESCRIPTION
}


#------------------------------ SCRIPT PRE-PROCESSING ------------------------------#
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
echo_colorchar "="
echo_center_text "$(echo_colorchar "*" "green" 5)  \t${blue}${underline}Creating Release for $VERSION - $VERSION_DESCRIPTION${normal}\t    $(echo_colorchar "*" "green" 5)"
echo_colorchar "-" "black"
echo ""


#------------------------------ CREATE RELEASE BRANCH ------------------------------#
RELEASE_BRANCH="release/$VERSION-${VERSION_DESCRIPTION//" "/-}" # space to hyphen
git checkout develop
git checkout -b $RELEASE_BRANCH


#------------------------------ VERSION STATS DIRECTORY ------------------------------#
VERSION_STATS_DIR="$PROJECT/stats/$VERSION"
mkdir -p $VERSION_STATS_DIR
echo_create $VERSION_STATS_DIR


#------------------------------ COVERAGE REPORT ------------------------------#
cd $PROJECT
# TODO: [2022/11/05] - Check if docker desktop is running
export ENVIRONMENT='development' # pytest needs this to run and will only ever be run in dev
coverage run --module pytest
coverage report -m > stats/$VERSION/coverage.txt
coverage json -o stats/$VERSION/coverage.json
coverage html -d stats/$VERSION/coverage_html/
echo_create "$VERSION_STATS_DIR/coverage.txt"
echo_create "$VERSION_STATS_DIR/coverage.json"


#------------------------------ TOKEI LINES OF CODE ------------------------------#
cd ../
tokei . --exclude .venv --exclude $PROJECT/backend/alembic/versions/ > $VERSION_STATS_DIR/lines_of_code.txt
echo_create "$VERSION_STATS_DIR/lines_of_code.txt"
tokei . --exclude .venv --exclude $PROJECT/backend/alembic/versions/ -o json > $VERSION_STATS_DIR/lines_of_code.json
echo_create "$VERSION_STATS_DIR/lines_of_code.json"


#------------------------------ WILY CODE COMPLEXITY ------------------------------#
# wily does not have json output at the moment
git stash
wily build .
wily diff . -r master > $VERSION_STATS_DIR/complexity.txt
echo_create "$VERSION_STATS_DIR/complexity.txt"
git stash pop


#------------------------------ UPDATE VERSIONS IN FILES ------------------------------#
poetry version $SEMVER
echo_update "pyproject.toml $CURRENT_VERSION" "$SEMVER"

echo "__version__ = '$SEMVER'" > $PROJECT/__init__.py
echo_update "$PROJECT/__init__.py $CURRENT_VERSION" "$SEMVER"


#------------------------------ COMMIT CHANGES AND CREATE GIT TAG ------------------------------#
git add -A
git commit -m "release: $VERSION - Create version stats"


#------------------------------ MERGE BRANCHES, TAG, AND PUSH ALL CHANGES------------------------------#
git checkout master
git merge $RELEASE_BRANCH
git tag $VERSION
git push
git push --tags
git checkout develop
git merge $RELEASE_BRANCH
git push


#------------------------------ REINSTALL PROGRAM ------------------------------#
poetry install


#------------------------------ SUCCESS ------------------------------#
echo ""
echo_colorchar "-" "black"
echo_center_text "${black}=====-----=====-----===== ${green} Successfully Created Release: $VERSION ${black} =====-----=====-----=====${normal}"
echo_colorchar "="
