pip install --upgrade pip
pip install -e .[dev]

coverage erase

echo "Wait for redis to be ready ..."
python ./check_redis_ready.py

if [ -z $1 ];
then
    coverage run -m pytest -v
else
    coverage run -m pytest -v -k $1
fi

failed=$?

coverage combine

exit $failed
