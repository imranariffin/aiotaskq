echo "Upgrade pip"
python -m pip install --quiet --upgrade pip

echo "Install dependencies"
pip install --quiet -e .[dev]

echo "Install sample apps"
PROJECT_DIR=$PWD envsubst < ./src/sample_apps/pyproject.template.toml > ./src/sample_apps/pyproject.toml
pip install --quiet -e file://$PWD/src/sample_apps/

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
