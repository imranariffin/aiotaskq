#!/bin/bash

venv=${1:-.venv}

python3.10 -m venv $venv
if [ "$?" != "0" ];
then
    echo "Please install Python 3.10.x"
    exit 1
fi

source $venv/bin/activate
echo "Using virtual environment $venv using $(python --version)"
deactivate
