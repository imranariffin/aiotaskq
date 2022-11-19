from aiotaskq import Aiotaskq


app = Aiotaskq(
    include=["sample_apps.simple_app.tasks_aiotaskq"],
)
