if [ -z $1 ];
then
    ./env_create.sh
    source ./env_activate.sh
    echo "Installing dependencies"
    source ./install_dependencies.sh > /dev/null
    pylint -v --rcfile ./.pylintrc src/aiotaskq
    failed_1=$?

    ./env_create.sh ./src/tests/.venv/
    source ./env_activate.sh ./src/tests/.venv/
    echo "Installing dependencies"
    source ./install_dependencies.sh ./src/tests/ > /dev/null
    pylint -v --rcfile ./.pylintrc.tests src/tests/
    failed_2=$?

    ./env_create.sh ./src/sample_apps/.venv/
    source ./env_activate.sh ./src/sample_apps/.venv/
    echo "Installing dependencies"
    source ./install_dependencies.sh ./src/sample_apps/ > /dev/null
    pylint -v --rcfile ./.pylintrc.sample_apps src/sample_apps/
    failed_3=$?

    [ $failed_1 -eq 0 ] && [ $failed_2 -eq 0 ] && [ $failed_3 -eq 0 ] && failed=0 || failed=1
else
    pylint -v $1
    failed=$?
fi

exit $failed
