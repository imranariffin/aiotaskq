coverage erase

if [ -z $1 ];
then
    pip install --upgrade pip
    pip install -e .[dev]
    coverage run -m pytest -v
else
    coverage run -m pytest --log-level=DEBUG --log-cli-level=DEBUG -s -vvv -k $1
fi

failed=$?

coverage combine --quiet

exit $failed
