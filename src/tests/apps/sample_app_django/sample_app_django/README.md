# Simple Django App

This simple Django App uses both Celery & aiotaskq to run the same logic inside workers, so you can
compare side by side the usage of these two libraries in this sample code and you can see that they are very similar in terms of usage.

You can also see that the difference in performance between these two. Run these two scripts one after the other:

0. [populate_db.sh](/src/tests/apps/sample_app_django/scripts/populate_db.sh)
1. [test_show_total_spending_celery.sh](/src/tests/apps/sample_app_django/scripts/test_show_total_spending_celery.sh)
2. [test_show_total_spending_aiotaskq.sh](/src/tests/apps/sample_app_django/scripts/test_show_total_spending_aiotaskq.sh)

As tested on my local machine, I got this results:
```bash
# Preparation
./src/tests/apps/sample_app_django/manage.py migrate
./src/tests/apps/sample_app_django/scripts/populate_db.sh

# Celery:
$ LOG_LEVEL=INFO ./src/tests/apps/sample_app_django/scripts/test_show_total_spending_celery.sh
Celery worker is ready with concurrency=4
...
2025-02-02 20:24:02,876 INFO     api.management.commands.show_total_spending_by_user CMD show_total_spending_by_user --celery...
2025-02-02 20:24:52,579 INFO     api.management.commands.show_total_spending_by_user Waiting for 10 tasks to finish
2025-02-02 20:24:04,437 INFO     api.management.commands.show_total_spending_by_user CMD show_total_spending_by_user --celery took 1.5609 seconds

# aiotaskq:
$ LOG_LEVEL=INFO ./src/tests/apps/sample_app_django/scripts/test_show_total_spending_aiotaskq.sh
aiotaskq worker is ready with concurrency=4
...
2025-02-02 20:20:44,752 INFO     api.management.commands.show_total_spending_by_user CMD show_total_spending_by_user --celery ...
2025-02-02 20:20:44,764 INFO     api.management.commands.show_total_spending_by_user Waiting for 10 tasks to finish
2025-02-02 20:20:44,876 INFO     api.management.commands.show_total_spending_by_user CMD show_total_spending_by_user --celery took 0.1231 seconds
```

Which shows that aiotaskq had much better throughput.

Check out the sample code within this folder and see for yourself. Also, try to run it and see the performance
comparison for yourself.
