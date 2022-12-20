# If not already inside it, clone the aiotaskq repository and cd into it
if [ "$(basename $PWD)" != "aiotaskq" ]; then
    git clone git@github.com:imranariffin/aiotaskq.git;
    cd aiotaskq
fi

# Let's say we want to run the first app (Simple App), which is located
# in `./src/sample_apps/src/sample_apps/simple_app/`. Update this env var APP as you'd like
# to choose your desired sample app.
APP=simple_app

# Create and activate virtual env specifically for the sample apps
./env_create.sh ./src/sample_apps/.venv/
source ./env_activate.sh ./src/sample_apps/.venv/

# Install sample_apps package from local file
./install_dependencies.sh ./src/sample_apps/

# Start redis and wait for it to be ready
docker-compose up -d redis
python ./check_redis_ready.py

# Run aiotaskq workers in background and wait for it be ready
echo "DEBUG START"
echo "Using $(python --version) from $(which python)"
pip freeze
echo "DEBUG END"
export LOG_LEVEL=${LOG_LEVEL:-INFO}
aiotaskq worker sample_apps.$APP --concurrency 4 &
sleep 2

# Prepare trap that kills celery workers that were running in background on script exit
trap "ps | grep aiotaskq | sed 's/^[ \t]*//;s/[ \t]*$//' | cut -d ' ' -f 1 | xargs kill -TERM" EXIT

# Run the the sample app
python -m sample_apps.$APP.app_aiotaskq || exit 1

# Confirm in the logs if the app is running correctly
