from aiotaskq import Aiotaskq


app = Aiotaskq(
    include=["simple_app.tasks_aiotaskq"],
)
