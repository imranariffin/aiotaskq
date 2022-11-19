# Sample apps

## Outline 
* [List of sample apps](#list-of-sample-apps)
* [Run a sample app with aiotaskq](#run-a-sample-app-with-aiotaskq)
* [Run a sample app with Celery](#run-a-sample-app-with-celery)

These are the sample apps that we use to test against and compare against
`Celery`. We define these sample apps in such a way that we can them both
using `aiotaskq` and `Celery` separately. This way we can compare them in terms
of performance, correctness, parity etc. This is also a way to document the
fact that `aiotaskq` is compatible with any framework that `Celery` supports, and
a recommended way to use `aiotaskq` alongside a specific framework.

## List of sample apps

- [x] [Simple App (No framework; explicit app instance)](/src/sample_apps/simple_app/)
- [ ] Simple App `FastAPI`
- [ ] Simple App `Django`
- [ ] Simple App `Starlette`
- [ ] Simple App `Starlite`
- [ ] Simple App `Sanic`
- [ ] Simple App `Quart`

## Run a sample app with aiotaskq

Feel free to run this inside of a `aiotaskq` repository. Copy-pasting
these commands to your terminal should work out of the box.

```bash
# If not already inside it, clone the aiotaskq repository and cd into it
[[ $(basename $PWD) == "aiotaskq" ]] || (git clone git@github.com:imranariffin/aiotaskq.git && cd aiotaskq)

# Let's say we want to run the first app (Simple App), which is located
# in `./sample_apps/simple_app/`. Update this env var APP as you'd like
# to choose your desired sample app.
APP=simple_app

# Create a new virtual env specifically for the sample apps
python -m venv ./sample_apps/.venv
source ./sample_apps/.venv/bin/activate

# Install sample_apps package from local file
pip install -e sample_apps

# Run aiotaskq workers in background and wait for it be ready
aiotaskq worker sample_apps.$APP --concurrency 4 &
sleep 2

# Run the the sample app
python -m sample_apps.$APP.app_aiotaskq

# Confirm in the logs if the app is running correctly

# Kill aiotaskq workers that were running in background
ps | grep aiotaskq | cut -d ' ' -f 1 | xargs kill -TERM
```

## Run a sample app with Celery

Now, if you want to run the sample app with `Celery` to see how `aiotaskq`
compares to it, do the following:

```bash
# If not already inside it, clone the aiotaskq repository and cd into it
[[ $(basename $PWD) == "aiotaskq" ]] || (git clone git@github.com:imranariffin/aiotaskq.git && cd aiotaskq)

# Let's say we want to run the first app (Simple App), which is located
# in `./sample_apps/simple_app/`. Update this env var APP as you'd like
# to choose your desired sample app.
APP=simple_app

# Create a new virtual env specifically for the sample apps
python -m venv ./sample_apps/.venv
source ./sample_apps/.venv/bin/activate

# Install sample_apps package from local file
pip install -e sample_apps

# Run Celery workers in background and wait for it to be ready
celery -A sample_apps.$APP worker --concurrency 4 &
sleep 2

# Run the the sample app
python -m sample_apps.$APP.app_celery

# Confirm in the logs if the app is running correctly

# Kill celery workers that were running in background
ps | grep celery | cut -d ' ' -f 1 | xargs kill -TERM
```
