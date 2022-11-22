from celery import Celery


app = Celery(
    include=["sample_apps.simple_app.tasks_celery"],
)
app.conf.broker_url = "redis://localhost:6379/0"
app.conf.result_backend = "redis://localhost:6379/0"
