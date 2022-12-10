#!/bin/bash

package=${1:-.}

if [[ "$package" = "." || "$package" = ".[dev]" ]]; then
    source ./enter_env.sh .venv
    pip install $package
elif [ "$package" = "./src/sample_apps/" ]; then
    source ./enter_env.sh ./src/sample_apps/.venv
    pip uninstall sample_apps -y
    rm -rf src/sample_apps/build/ src/sample_apps/sample_apps.egg-info/
    PROJECT_DIR=$PWD envsubst < ./src/sample_apps/pyproject.template.toml > ./src/sample_apps/pyproject.toml
elif [ "$package" = "./src/tests/" ]; then
    source ./enter_env.sh ./src/tests/.venv
    pip uninstall tests aiotaskq sample_apps -y
    rm -rf src/tests/build/ src/tests/tests.egg-info/ \
        src/sample_apps/build/ src/sample_apps/sample_apps.egg-info/ \
        src/aiotaskq/build/ src/aiotaskq/aiotaskq.egg-info/
    PROJECT_DIR=$PWD envsubst < ./src/tests/pyproject.template.toml > ./src/tests/pyproject.toml
else
    echo Package $package not recognized. Aborting.
    exit 1
fi

echo "Using $(pip --version)"
echo "Installing $(realpath $package) ..."
pip install --no-cache-dir $package
