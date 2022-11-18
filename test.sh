PROJECT_DIR=$PWD envsubst < ./sample_apps/simple_app/pyproject.template.toml > ./sample_apps/simple_app/pyproject.toml

coverage erase

if [ -z $1 ];
then
    coverage run -m pytest -v
else
    coverage run -m pytest -vvv -k $1 -s
fi

failed=$?

coverage combine

exit $failed
