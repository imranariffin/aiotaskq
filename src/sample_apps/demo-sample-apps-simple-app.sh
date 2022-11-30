# If not already inside it, clone the aiotaskq repository and cd into it
[[ $(basename $PWD) == "aiotaskq" ]] || (git clone git@github.com:imranariffin/aiotaskq.git && cd aiotaskq)

# Let's say we want to run the first app (Simple App), which is located
# in `./src/sample_apps/simple_app/`. Update this env var APP as you'd like
# to choose your desired sample app.
APP=simple_app

# Create a new virtual env specifically for the sample apps
rm -rf ./src/sample_apps/.venv || echo ""
python3.10 -m venv ./src/sample_apps/.venv
source ./src/sample_apps/.venv/bin/activate
echo "Using $(python --version)"

# Install sample_apps package from local file
python -m pip install --no-cache-dir --upgrade pip
PROJECT_DIR=$PWD envsubst < ./src/sample_apps/pyproject.template.toml > ./src/sample_apps/pyproject.toml
pip install --no-cache-dir file://$PWD/src/sample_apps

# Start redis and wait for it to be ready
docker-compose up -d redis
python ./check_redis_ready.py

# Run aiotaskq workers in background and wait for it be ready
aiotaskq --version
aiotaskq worker sample_apps.$APP --concurrency 4 &
sleep 2

# Run the the sample app
python -m sample_apps.$APP.app_aiotaskq

# Confirm in the logs if the app is running correctly

# Kill aiotaskq workers that were running in background
ps | grep aiotaskq | sed 's/^[ \t]*//;s/[ \t]*$//' | cut -d ' ' -f 1 | xargs kill -TERM
