import os

from aiotaskq import App

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sample_app_django.settings')


app = App()

app.autodiscover_tasks()
