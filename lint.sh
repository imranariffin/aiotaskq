if [ -z $1 ];
then
    pylint -v --rcfile ./.pylintrc src/aiotaskq
    failed_1=$?

    pylint -v --rcfile ./.pylintrc.tests src/tests/
    failed_2=$?

    pylint -v --rcfile ./.pylintrc.sample_apps src/sample_apps/
    failed_3=$?

    [ $failed_1 -eq 0 ] && [ $failed_2 -eq 0 ] && [ $failed_3 -eq 0 ] && failed=0 || failed=1
else
    pylint -v $1
    failed=$?
fi

exit $failed
