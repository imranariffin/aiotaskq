#! /bin/bash

cd "$(dirname "$0")"/../

AIOTASKQ_LOG_LEVEL=INFO LOG_LEVEL=INFO coverage run -m aiotaskq \
    worker sample_app_django \
    --concurrency 4 &
WPID=$!
echo "aiotaskq worker is ready with concurrency=4"

trap "kill -TERM $WPID" SIGINT SIGTERM EXIT

# Wait until aiotaskq is ready (ie having "num_child_process" == "--concurrency")
while :
do
    NCHILD=$(ps -eo ppid= | grep -Fwc $WPID)
    if [ $NCHILD == "4"  ];
    then
        break
    fi
    sleep 0.05
done

coverage run ./manage.py show_total_spending_by_user --aiotaskq
