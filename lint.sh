pip install --upgrade pip
pip install -e .[dev]

if [ -z $1 ];
then
    pylint -v --rcfile ./.pylintrc --ignore-paths=src/aiotaskq/tests/* src/aiotaskq
    failed_2=$?

    pylint -v --rcfile ./.pylintrc.test src/aiotaskq/tests/
    failed_1=$?

    [ $failed_1 -eq 0 ] && [ $failed_2 -eq 0 ] && failed=0 || failed=1
else
    pylint -v $1
    failed=$?
fi

exit $failed
