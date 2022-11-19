from types import ModuleType

import pytest

import aiotaskq
from aiotaskq.task import Task
from aiotaskq.app import Aiotaskq

from sample_apps.simple_app.aiotaskq import app as simple_app


@pytest.mark.parametrize(
    "valid_import_path,app_expected",
    [
        (
            # Case 1: Tasks are defined inside a module without using explicit Aiotaskq
            # instance, and
            "sample_apps.simple_app.aiotaskq",
            # We should instantiate Aiotaskq using the module path.
            simple_app,
        ),
        # (
        #     # Case 2: Tasks are defined using an explicit Aiotaskq instance, and 
        #     "aiotaskq.tests.apps.simple_app_encapsulated",
        #     # We should instantiate Aiotaskq from the import path to the instance.
        #     aiotaskq.tests.apps.simple_app_encapsulated.aiotaskq.app,
        # ),
        # (
        #     # Case 3: Tasks are defined using an explicit Aiotaskq instance in a default
        #     # file name ("aiotaskq.py"), and
        #     "aiotaskq.tests.apps.simple_app_encapsulated.aiotaskq:app",
        #     # We should instantiate Aiotaskq from the import path to the instance
        #     # using the ":" pattern (this pattern is useful to differentiate between
        #     # a module and an object).
        #     aiotaskq.tests.apps.simple_app_encapsulated.aiotaskq.app,
        # ),
        # (
        #     # Case 4: Tasks are defined using an explicit Aiotaskq instance in
        #     # a non-default file name ("some_module_name.py"), and
        #     "aiotaskq.tests.apps.simple_app_encapsulated_2.some_file_name:some_app",
        #     # We should instantiate Aiotaskq from the import path to the instance
        #     # using the ":" pattern (this pattern is useful to differentiate between
        #     # a module and an object)".
        #     aiotaskq.tests.apps.simple_app_encapsulated_2.some_file_name.some_app,
        # ),
        # (
        #     # Case 5: Tasks are defined using an explicit Aiotaskq instance in a non-default
        #     # file name ("some_module_name.py"), and
        #     "aiotaskq.tests.apps.simple_app_encapsulated_2.some_file_name",
        #     # We should instantiate Aiotaskq from the import path to the instance
        #     # using the ":" pattern (this pattern is useful to differentiate between
        #     # a module and an object)".
        #     aiotaskq.tests.apps.simple_app_encapsulated_2.some_file_name.some_app,
        # ),
    ],
)
def test_valid_app_import_path(valid_import_path: str, app_expected: ModuleType):
    # Given a valid import path

    # When instantiating an Aiotaskq from the import path
    app_actual = Aiotaskq.from_import_path(valid_import_path)

    # Then the instantiated Aiotaskq object should be loaded with the tasks
    assert isinstance(app_actual.add, Task)
    assert app_expected.add == app_actual.task_map["add"] == app_actual.add  # type: ignore
