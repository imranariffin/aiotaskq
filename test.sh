echo "Upgrade pip"
pip install --quiet --upgrade pip

echo "Install sample projects"
PROJECT_DIR=$PWD envsubst < ./sample_apps/simple_app/pyproject.template.toml > ./sample_apps/simple_app/pyproject.toml
pip install --quiet -e ./sample_apps/simple_app/

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
