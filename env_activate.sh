#!/bin/bash

if hash grealpath 2>/dev/null; then
  REALPATH="grealpath"
else
  REALPATH="realpath"
fi

env=${1:-.venv}
env=$(realpath $env)
echo env=$env

if [ -z "$VIRTUAL_ENV" ]; then
    echo "Entering virtual environment '$env'"
    source $env/bin/activate || exit 1
else
    if [ "$VIRTUAL_ENV" != "$env" ]; then
        echo "Switching virtual environment from '$VIRTUAL_ENV' to '$env'"
        source $env/bin/activate || exit 1
    else
        echo "Already in virtual environment '$VIRTUAL_ENV'"
    fi
fi
