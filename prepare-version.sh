################################################################################
# ACTIONS #
# 1. Create directory `euphoria/stats/{version}`
# 2. Update `pyproject.toml`
# 3. Update `euphoria/__init__.py`
# 4. Run pytest and create coverage report
# 5. Run tokei and create lines of code report
# 6. Run wily and create code complexity report

# DEPENDENCIES #
# tokei
# wily

# USAGE #
# Run as ./prepare-version.sh {version} "Version Description"
# MUST leave off the v in version:
# YES {0.5.0}
# NO {v0.5.0}

# EXAMPLE #
# ./prepare-version.sh 0.5.2 "Add API Endpoint"
################################################################################

# Commandline Colors
bold=$(tput bold)
blue=$(tput setaf 4)
green=$(tput setaf 2)
red=$(tput setaf 1)
normal=$(tput sgr0)

# SEMVER is format: 1.1.1 -> useful for string replacement in files
# VERISON is format: v1.1.1 -> useful for folder and file names
SEMVER=$1
VERSION="v$1"
VERSION_DESCRIPTION=$2

echo "${bold}${blue}----- Preparing Release for $VERSION - $VERSION_DESCRIPTION -----${normal}"

# Make version stats directory
mkdir -p euphoria/stats/$VERSION

# Coverage Report
echo "${green}Creating Pytest Coverage Report${normal}"
cd euphoria/
coverage report -m > stats/$VERSION/coverage.txt
coverage json -o stats/$VERSION/coverage.json

# Lines of Code Files
echo "${green}Creating Lines of Code Files${normal}"
cd ../
tokei . --exclude .venv --exclude euphoria/backend/alembic/versions/ > euphoria/stats/$VERSION/lines_of_code.txt
tokei . --exclude .venv --exclude euphoria/backend/alembic/versions/ -o json > euphoria/stats/$VERSION/lines_of_code.json

# Wily Code Complexity
# wily does not have json output at the moment
echo "${green}Creating Code Complexity Report${normal}"
wily build .
wily diff . -r master > euphoria/stats/$VERSION/complexity.txt

echo "${green}Version stats saved: euphoria/stats/$VERSION${normal}"

# Update the version in pyproject.toml
poetry version $SEMVER

# Update the version in euphoria/__init__.py
echo "__version__ = '$SEMVER'" > euphoria/__init__.py

echo "${green}Updated version in pyproject.toml${normal}"
echo "${green}Updated version in euphoria/__init__.py${normal}"
echo "${blue}Finished with Release${normal}"