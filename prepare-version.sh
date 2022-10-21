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

# SEMVER is format: 1.1.1 -> useful for string replacement in files
# VERISON is format: v1.1.1 -> useful for folder and file names
SEMVER=$1
VERSION="v$1"
VERSION_DESCRIPTION=$2

echo "Preparing Release for version $SEMVER"

# Make version directory
mkdir -p euphoria/stats/$VERSION
echo "Version Stats Directory Created"

# Update the version in pyproject.toml
sed -ri "s/version = \"[0-9]+\.[0-9]+\.[0-9]+\"/version = \"$SEMVER\"/" pyproject.toml
echo "Version updated in pyproject.toml"

# Update the version in euphoria/__init__.py
echo "__version__ = '$SEMVER'" > euphoria/__init__.py
echo "Updated version in euphoria/__init__.py"

# Pytest and Coverage Report
cd euphoria/
pwd
pytest --cov
coverage report -m > stats/$VERSION/coverage.txt
coverage json -o stats/$VERSION/coverage.json
echo "Created Pytest Coverage Report"

# Lines of Code Files
cd ../
pwd
tokei . --exclude .venv --exclude euphoria/backend/alembic/versions/ > euphoria/stats/$VERSION/lines_of_code.txt
tokei . --exclude .venv --exclude euphoria/backend/alembic/versions/ -o json > euphoria/stats/$VERSION/lines_of_code.json
echo "Created Lines of Code Files"

# Wily Code Complexity
# wily does not have json output at the moment
wily build .
wily diff . -r master > euphoria/stats/$VERSION/complexity.txt
echo "Created Code Complexity Report"
