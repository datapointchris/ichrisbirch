
# Run in .../euphoria/
# ./create_version.sh v0.5.0 "FastAPI Integration"

pwd
# Get the version from command line
VERSION=$1
VERSION_DESCRIPTION=$2
echo "Creating Release for: $VERSION"

# Make version directory
mkdir -p euphoria/version_stats/$VERSION
echo "Directory Created"

cd euphoria/
pwd

# Update the version 
echo "__version__ = '$VERSION'" > __init__.py
echo "Updated version"

cd backend/
pwd

# Dev postgres has to be running
# Create alembic revision
alembic revision --autogenerate -m $VERSION
echo "Created Alembic Revision"

cd ../
pwd

# Create a Coverage Report
pytest --cov
coverage report -m > version_stats/$VERSION/coverage.txt
coverage json -o version_stats/$VERSION/coverage.json
echo "Created Pytest Coverage Report"

cd ../
pwd

# Create a new stats file json and text
tokei . --exclude .venv --exclude euphoria/backend/alembic/versions/ > euphoria/version_stats/$VERSION/lines_of_code.txt
tokei . --exclude .venv --exclude euphoria/backend/alembic/versions/ -o json > euphoria/version_stats/$VERSION/lines_of_code.json
echo "Created Lines of Code Files"


# Run Wily Code Complexity
# wily does not have json output at the moment
wily diff . -r master > euphoria/version_stats/$VERSION/complexity.txt
echo "Created Code Complexity Report"

# Commit version stats files and create a version tag
git commit -am "release: $VERSION - $VERSION_DESCRIPTION"
echo "Add and Commit Reports"

# Create a git tag for the commit
git tag $VERSION
echo "Created git tag for release"

# Push branch and tags
# git push --tags
echo "Changes pushed to git"