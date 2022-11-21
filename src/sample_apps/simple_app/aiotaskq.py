from aiotaskq import Aiotaskq


app = Aiotaskq(
    include=["sample_apps.simple_app.tasks_aiotaskq"],
)
# OR can use any variable name for the app instance
some_app = app
# Including `aiotaskq`
aiotaskq = app
