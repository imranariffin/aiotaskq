#! /bin/bash

docker-compose -f ./docker-compose.yml up --detach redis
./env_create.sh ./src/tests/.venv/
source ./env_activate.sh ./src/tests/.venv/
./install_dependencies.sh ./src/tests/
python ./check_redis_ready.py
