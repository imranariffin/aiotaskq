#!/bin/bash

py_version=$(python3 --version | grep -o 3.10)

if [ "$py_version" != "3.10" ]; then
    echo "Please install Python 3.10.x"
    exit 1
fi

venv=${1:-.venv}
python3 -m venv $venv
source $venv/bin/activate

echo "Using $(python --version)"
echo "Using $(pip --version)"
