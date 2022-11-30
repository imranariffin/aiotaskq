# If not already inside it, clone the aiotaskq repository and cd into it
[[ $(basename $PWD) == "aiotaskq" ]] || (git clone git@github.com:imranariffin/aiotaskq.git && cd aiotaskq)

# Create a new virtual env specifically for the sample apps
python3.10 -m venv ./src/sample_apps/.venv
source ./src/sample_apps/.venv/bin/activate
echo "Using $(python --version)"

# Start redis and wait for it to be ready
docker-compose up --detach redis
python ./check_redis_ready.py

# Let's say we want to run the first app (Simple App), which is located
# in `./src/sample_apps/simple_app/`. Update this env var APP as you'd like
# to choose your desired sample app.
APP=simple_app

# Install sample_apps package from local file
python3 -m pip install --upgrade pip
PROJECT_DIR=$PWD envsubst < ./src/sample_apps/pyproject.template.toml > ./src/sample_apps/pyproject.toml
pip install -e ./src/sample_apps

# Run Celery workers in background and wait for it to be ready
celery -A sample_apps.$APP worker --concurrency 4 &
sleep 2

# Run the the sample app
python3.10 -m sample_apps.$APP.app_celery

# Confirm in the logs if the app is running correctly

# Kill celery workers that were running in background
ps | grep celery | sed 's/^[ \t]*//;s/[ \t]*$//' | cut -d ' ' -f 1 | xargs kill -TERM
