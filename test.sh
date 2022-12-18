echo "Enter virtual environment for testing"
source ./enter_env.sh ./src/tests/.venv
source ./install_dependencies.sh ./src/tests/
export LOG_LEVEL=${LOG_LEVEL:-INFO}
echo "Using $(pip --version)"

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
