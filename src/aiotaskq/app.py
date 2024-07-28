"""
Define the aiotaskq application instance.

This app instance provides access to all tasks defined within the application.
"""

from importlib import import_module
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from .task import Task


class App:
    """Define the aiotaskq application instance."""

    _task_registry: dict[str, "Task"] = {}

    def __getattribute__(self, name: str, /) -> Any:
        """Get access to all task instances defined within the application."""

        task_registry = object.__getattribute__(self, "_task_registry")
        if name in task_registry:
            return task_registry[name]
        return object.__getattribute__(self, name)

    def autodiscover_tasks(self, tasks_module_name: str = "tasks"):
        """
        Search for all tasks defined within the application and import them.

        The tasks are expected to be defined in files named as "tasks.py".
        """

        import django  # pylint: disable=import-outside-toplevel
        from django.apps import apps  # pylint: disable=import-outside-toplevel

        django.setup()

        module_names: list[str] = [config.name for config in apps.get_app_configs()]
        for module_name in module_names:
            _ = import_module(module_name)
            try:
                _ = import_module(f"{module_name}.{tasks_module_name}")
            except ModuleNotFoundError:
                pass
            else:
                pass
