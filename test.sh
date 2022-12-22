echo "Enter virtual environment for testing"
source ./env_activate.sh ./src/tests/.venv
export LOG_LEVEL=${LOG_LEVEL:-INFO}
python --version

echo "Erase previous coverage files"
coverage erase

echo "Run tests"
if [ -z $1 ];
then
    coverage run -m pytest -vvv -s
else
    coverage run -m pytest -vvv -k $1 -s
fi
failed=$?

echo "Combine coverage files"
coverage combine

exit $failed
