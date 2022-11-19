# echo "Upgrade pip"
# pip install --quiet --upgrade pip

# echo "Install dependencies"
# pip install -v --no-cache-dir -e .[dev]

echo "Install sample apps"
PROJECT_DIR=$PWD envsubst < ./sample_apps/pyproject.template.toml > ./sample_apps/pyproject.toml
pip install --quiet --no-cache-dir -e file://$PWD/sample_apps/

echo "Erase previous coverage files"
coverage erase

echo "Run tests"
if [ -z $1 ];
then
    coverage run -m pytest -v
else
    coverage run -m pytest -vvv -k $1 -s
fi
failed=$?

echo "Combine coverage files"
coverage combine

exit $failed
