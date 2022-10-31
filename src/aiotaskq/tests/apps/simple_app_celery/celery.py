from celery import Celery


app = Celery(
    include=["aiotaskq.tests.apps.simple_app_celery.tasks"],
)
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'

if __name__ == "__main__":
    app.start()
