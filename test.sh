pip install --upgrade pip
pip install -e .[dev]

coverage erase

if [ -z $1 ];
then
    coverage run -m pytest -v
else
    coverage run -m pytest -v -k $1
fi

failed=$?

coverage combine

exit $failed
