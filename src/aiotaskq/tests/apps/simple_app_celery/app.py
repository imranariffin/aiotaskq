from aiotaskq.tests.apps.simple_app_celery.tasks import get_formula
from .celery import app


if __name__ == "__main__":
    formula = get_formula()
    ret = formula.apply_async().get()
    assert ret == 14
