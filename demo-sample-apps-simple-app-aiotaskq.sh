# If not already inside it, clone the aiotaskq repository and cd into it
if [ "$(basename $PWD)" != "aiotaskq" ]; then
    git clone git@github.com:imranariffin/aiotaskq.git;
    cd aiotaskq
fi

# Let's say we want to run the first app (Simple App), which is located
# in `./src/sample_apps/src/sample_apps/simple_app/`. Update this env var APP as you'd like
# to choose your desired sample app.
APP=simple_app

# Enter virtual env specifically for the sample apps
source ./env_activate.sh ./src/sample_apps/.venv

# Install sample_apps package from local file
./install_dependencies.sh ./src/sample_apps/

# Start redis and wait for it to be ready
docker-compose up -d redis
python ./check_redis_ready.py

# Run aiotaskq workers in background and wait for it be ready
echo "DEBUG START"
echo "Using $(python --version) from $(which python)"
echo "DEBUG END"
export LOG_LEVEL=${LOG_LEVEL:-INFO}
aiotaskq worker sample_apps.$APP --concurrency 4 &
sleep 2

# Run the the sample app
python -m sample_apps.$APP.app_aiotaskq

# Confirm in the logs if the app is running correctly

# Kill aiotaskq workers that were running in background
ps | grep aiotaskq | sed 's/^[ \t]*//;s/[ \t]*$//' | cut -d ' ' -f 1 | xargs kill -TERM
