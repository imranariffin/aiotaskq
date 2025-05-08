coverage erase

echo "Running unit tests ..."

if [ -z $1 ];
then
    pip install --upgrade pip
    pip install -e .[dev]
    coverage run -m pytest -v
else
    coverage run -m pytest --log-level=DEBUG --log-cli-level=DEBUG -s -vvv -k $1
fi

echo "Running unit tests DONE"

failed=$?

# TODO @imranariffin: Move this sample code tests to a different file
#   #25

echo "Running tests against sample codes ..."

echo "Creating a fresh sample_app_django db ..."
PGPASSWORD=postgres dropdb -h localhost -U postgres sample_app_django 2> /dev/null;
PGPASSWORD=postgres createdb -h localhost -U postgres sample_app_django || exit $?
echo "Creating a fresh sample_app_django db DONE"

echo "Migrating the sample_app_django db ..."
coverage run \
    ./src/tests/apps/sample_app_django/manage.py migrate;
echo "Migrating the sample_app_django db DONE"

echo "Populating the sample_app_django db ..."
./src/tests/apps/sample_app_django/scripts/populate_db.sh
echo "Populating the sample_app_django db DONE"

echo "Running test: show_total_spending_by_user --celery ..."
./src/tests/apps/sample_app_django/scripts/test_show_total_spending_celery.sh
echo "Running test: show_total_spending_by_user --celery DONE"

echo "Running test: show_total_spending_by_user --aiotaskq ..."
./src/tests/apps/sample_app_django/scripts/test_show_total_spending_aiotaskq.sh
echo "Running test: show_total_spending_by_user --aiotaskq DONE"

DIFF=$(\
    diff \
    ./src/tests/apps/sample_app_django/out-celery.json \
    ./src/tests/apps/sample_app_django/out-aiotaskq.json \
)
if [ -z $DIFF ]; then
    echo "Tests against sample codes SUCCEEDED"
else
    echo "Tests against sample codes FAILED"
    echo "Results diff:"
    diff \
        ./src/tests/apps/sample_app_django/out-celery.json \
        ./src/tests/apps/sample_app_django/out-aiotaskq.json \
        | head -10
    echo "..."
    diff \
        ./src/tests/apps/sample_app_django/out-celery.json \
        ./src/tests/apps/sample_app_django/out-aiotaskq.json \
        | tail -10
    failed=1
fi

echo "Running tests against sample codes DONE"

mv ./src/tests/apps/sample_app_django/.coverage.* ./

coverage combine --quiet

exit $failed
