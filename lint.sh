pip install --upgrade pip
pip instal pytest
pip install pytest-asyncio
pip install pylint

if [ -z $1 ];
then
    pylint -v src/aiotaskq --ignore-paths=src/aiotaskq/tests/* 
    pylint -v --rcfile ./.pylintrc.test src/aiotaskq/tests/
else
    pylint -v $1
fi
