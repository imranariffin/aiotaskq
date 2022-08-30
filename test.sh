pip install --upgrade pip
pip install pytest
pip install pytest-asyncio
pip install coverage

coverage erase

if [ -z $1 ];
then
    coverage run -m pytest -v -s
else
    coverage run -m pytest -v -s -k $1
fi

coverage combine
