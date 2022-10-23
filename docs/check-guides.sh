# Scripts to check if the code examples in the guides are
# correct. A check should follow this template:
#
# 1. echo -e "\n===\n<Some specific title from DOCS.md>\n===\n"
# 2. Some startup processes to run in background e.g. server & worker.
# Ensure pids are saved to a variable so we can kill them in the final
# step.
# 3. Run the check and set $failed variable to "1" if fails.
# 4. Kill the background processes, preferably using TERM so child
# processes are also killed. For example, see existing checks.

set -x

echo -e "\n===\nExample usage 1: Sample usage - Simple App\n===\n"
echo "Run worker in the background & save the pid ..."
python -m aiotaskq worker aiotaskq.tests.apps.simple_app.tasks & worker_pid=$!
echo "Run server in the background & save the pid ..."
python -m aiotaskq.tests.apps.simple_app.app & server_pid=$!
echo "Wait 1 second(s) for server & worker to be ready ..."
sleep 1
echo "Run the app and check the output ..."
output=$(python -m aiotaskq.tests.apps.simple_app.app)
set +x
test "$output" = "Hello World"
if [ "$?" = "0" ]
then
  echo -e "🎉🎉🎉\n\nPass :D"
else
  echo -e "⛔⛔⛔\n\nFailed :("
  failed="1"
fi
set -x
echo "Kill the server & worker processes ..."
kill -TERM $worker_pid && unset worker_pid

echo -e "\n===\nExample usage 3: Sample usage - Starlette Simple App\n===\n"
echo "Run worker in the background & save the pid ..."
python -m aiotaskq worker aiotaskq.tests.apps.simple_app_starlette.tasks & worker_pid=$!
echo "Run server in the background & save the pid ..."
python -m aiotaskq.tests.apps.simple_app_starlette.app & server_pid=$!
echo "Wait 1 second(s) for server & worker to be ready ..."
sleep 1
echo "Make a request to one of the endpoints & check if correct ..."
response=$(curl --silent -X POST \
  http://127.0.0.1:8000/add \
  -H 'Content-Type: application/json' \
  -d '{"x": 123, "y": 456}'
)
set +x
test "$response" = "579"
if [ "$?" = "0" ]
then
  echo -e "🎉🎉🎉\n\nPass :D"
else
  echo -e "⛔⛔⛔\n\nFailed :("
  failed="1"
fi
set -x
echo "Kill the server & worker processes"
kill -TERM $server_pid $worker_pid && unset server_pid worker_pid

if [ "$failed" = "1" ]
then
  exit 1
fi
