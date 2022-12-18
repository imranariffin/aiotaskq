#!/bin/bash

package=${1:-.}

if [[ "$package" = "." || "$package" = ".[dev]" ]]; then
    :
elif [ "$package" = "./src/sample_apps/" ]; then
    pip uninstall sample_apps -y
    rm -rf ${package}build/ ${package}/sample_apps.egg-info/
    PROJECT_DIR=$PWD envsubst < ${package}/pyproject.template.toml > ${package}/pyproject.toml
elif [ "$package" = "./src/tests/" ]; then
    pip uninstall tests aiotaskq sample_apps -y
    rm -rf src/tests/build/ src/tests/tests.egg-info/ \
        src/sample_apps/build/ src/sample_apps/sample_apps.egg-info/ \
        src/aiotaskq/build/ src/aiotaskq/aiotaskq.egg-info/
    PROJECT_DIR=$PWD envsubst < ./src/tests/pyproject.template.toml > ./src/tests/pyproject.toml
else
    echo Custom package $package detected.
fi

echo "Using $(pip --version)"
echo "Installing $(realpath $package) ..."
pip install --upgrade pip
pip install --no-cache-dir $package
