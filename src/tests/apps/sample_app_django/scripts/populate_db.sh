#! /bin/bash

# Go back to project root so that coverage data will be combined into
# to the correct `.coverage` instead of creating a new separate one
cd "$(dirname "$0")"/../

echo "Populating the db ..."
coverage run \
    ./manage.py populate_db \
    --n-users 1000 \
    --n-orders-per-user 100 \
    --from-scratch
