#!/bin/bash

py_version=$(python3 --version | grep -o 3.10)

if [ "$py_version" != "3.10" ]; then
    echo "Please install Python 3.10.x"
    exit 1
fi

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip --quiet
pip install -e . --quiet

python --version
pip --version
