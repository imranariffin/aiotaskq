#! /bin/bash

cd "$(dirname "$0")"/../

LOG_LEVEL=INFO coverage run -m celery -A sample_app_django \
    worker \
    --concurrency 4 \
    --loglevel WARNING &
WPID=$!
echo "Celery worker is ready with concurrency=4"

trap "kill -TERM $WPID" SIGINT SIGTERM EXIT

coverage run ./manage.py show_total_spending_by_user --celery
