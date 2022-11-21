from types import ModuleType

import pytest

from aiotaskq.task import Task
from aiotaskq.app import Aiotaskq

from sample_apps.simple_app.aiotaskq import app as simple_app
from sample_apps.simple_app_implicit_instance import app_aiotaskq as simple_app_implicit_instance


@pytest.mark.parametrize(
    "valid_import_path,app_expected",
    [
        (
            # Case 1.1.1: Tasks are defined using an explicit Aiotaskq instance with
            # default name "app", and
            "sample_apps.simple_app.aiotaskq:app",
            # We should instantiate Aiotaskq from the import path to the instance.
            simple_app,
        ),
        (
            # Case 1.1.2: Tasks are defined using an explicit Aiotaskq instance with
            # default name "app", and
            "sample_apps.simple_app.aiotaskq.app",
            # We should instantiate Aiotaskq from the import path to the instance.
            simple_app,
        ),
        (
            # Case 1.1.3: Tasks are defined using an explicit Aiotaskq instance with custom name, and
            "sample_apps.simple_app.aiotaskq:some_app",
            # We should instantiate Aiotaskq from the import path to the instance.
            simple_app,
        ),
        (
            # Case 1.2: Tasks are defined using an explicit Aiotaskq instance, and
            "sample_apps.simple_app.aiotaskq",
            # We should instantiate Aiotaskq from the import path to the instance.
            simple_app,
        ),
        (
            # Case 1.3: Tasks are defined using an explicit Aiotaskq instance, and
            "sample_apps.simple_app",
            # We should instantiate Aiotaskq from the import path to the instance.
            simple_app,
        ),
        (
            # Case 2: Tasks are defined inside a module without using explicit Aiotaskq
            # instance, and
            "sample_apps.simple_app_implicit_instance.app_aiotaskq",
            # We should instantiate a new Aiotaskq instance using the module path.
            simple_app_implicit_instance,
        ),
        # (
        #     # Case 3: Tasks are defined using an explicit Aiotaskq instance in a default
        #     # file name ("aiotaskq.py"), and
        #     "tests.apps.simple_app_encapsulated.aiotaskq:app",
        #     # We should instantiate Aiotaskq from the import path to the instance
        #     # using the ":" pattern (this pattern is useful to differentiate between
        #     # a module and an object).
        #     tests.apps.simple_app_encapsulated.aiotaskq.app,
        # ),
        # (
        #     # Case 4: Tasks are defined using an explicit Aiotaskq instance in
        #     # a non-default file name ("some_module_name.py"), and
        #     "tests.apps.simple_app_encapsulated_2.some_file_name:some_app",
        #     # We should instantiate Aiotaskq from the import path to the instance
        #     # using the ":" pattern (this pattern is useful to differentiate between
        #     # a module and an object)".
        #     tests.apps.simple_app_encapsulated_2.some_file_name.some_app,
        # ),
        # (
        #     # Case 5: Tasks are defined using an explicit Aiotaskq instance in a non-default
        #     # file name ("some_module_name.py"), and
        #     "tests.apps.simple_app_encapsulated_2.some_file_name",
        #     # We should instantiate Aiotaskq from the import path to the instance
        #     # using the ":" pattern (this pattern is useful to differentiate between
        #     # a module and an object)".
        #     tests.apps.simple_app_encapsulated_2.some_file_name.some_app,
        # ),
    ],
)
def test_valid_app_import_path(valid_import_path: str, app_expected: ModuleType):
    # Given a valid import path

    # When instantiating an Aiotaskq from the import path
    app_actual = Aiotaskq.from_import_path(valid_import_path)

    # Then the instantiated Aiotaskq object should be loaded with the tasks
    assert isinstance(app_actual.add, Task)
    assert app_actual.add == app_actual.task_map["add"] == app_expected.add # type: ignore
    assert app_actual.add(ls=[2, 3]) == 5
    assert isinstance(app_actual.times, Task)
    assert app_actual.times == app_actual.task_map["times"] == app_expected.times # type: ignore
    assert app_actual.times(x=2, y=3) == 6
