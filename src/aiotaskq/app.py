"""Define the logic to create an aiotaskq app instance."""

import importlib
import inspect
import typing as t

from .exceptions import AppImportError
from .task import Task

if t.TYPE_CHECKING:  # pragma: no cover
    from types import ModuleType


class Aiotaskq:
    """Encapsulate the whole application logic."""

    import_path: str
    task_map: dict[str, Task] = {}

    def __init__(
        self,
        import_path: t.Optional[str] = None,
        tasks: t.Optional[list[Task]] = None,
        include: t.Optional[list[str]] = None,
    ):
        self.import_path = (
            import_path
            if import_path is not None
            else inspect.getmodule(self).__name__  # type: ignore
        )
        self.task_map = {task_.__name__: task_ for task_ in tasks} if tasks else {}
        if include is not None:
            for module_path in include:
                module = importlib.import_module(module_path)
                tasks = self._extract_tasks(app_or_module=module)
                self.task_map.update({task_.__name__: task_ for task_ in tasks})

    def __getattribute__(self, attr_name: str) -> t.Any:
        try:
            return object.__getattribute__(self, attr_name)
        except AttributeError:
            # The desired attribute could be a Task.
            task_map: dict[str, Task] = object.__getattribute__(self, "task_map")
            try:
                return task_map[attr_name]
            except KeyError as exc:
                raise AttributeError from exc

    @classmethod
    def from_import_path(cls, app_or_module_path: str) -> "Aiotaskq":
        """Return an Aiotaskq instance instantied from the provided app_path string."""

        app_import_error_msg = f"App or module path `{app_or_module_path}` is not valid."

        app_attr_name: t.Optional[str] = None
        app: "Aiotaskq"
        if ":" in app_or_module_path:
            # Import path points to an Aiotaskq instance -- use it.
            module_path, app_name = app_or_module_path.split(":")

            try:
                module = importlib.import_module(module_path)
            except ImportError as exc:
                raise AppImportError(app_import_error_msg) from exc

            app = getattr(module, app_name)
        else:
            app_or_module: "Aiotaskq | ModuleType"

            try:
                app_or_module = importlib.import_module(f"{app_or_module_path}.aiotaskq")
            except ImportError:
                try:
                    app_or_module = importlib.import_module(app_or_module_path)
                except ModuleNotFoundError:
                    module_path, _, app_attr_name = app_or_module_path.rpartition(".")
                    try:
                        app_or_module = importlib.import_module(module_path)
                    except (ModuleNotFoundError, ImportError) as exc:
                        raise AppImportError(app_import_error_msg) from exc
                    app = getattr(app_or_module, app_attr_name)
                except ImportError as exc:
                    raise AppImportError(app_import_error_msg) from exc

            if (
                app_or_module is not None
                and app_attr_name is not None
                and hasattr(app_or_module, app_attr_name)
                and isinstance(getattr(app_or_module, app_attr_name), Aiotaskq)
            ):
                # Import path points to a module that contains an Aiotaskq instance named as
                # `<app_attr_name>` (or the default "app") -- retrieve the instance and use it.
                app = getattr(app_or_module, app_attr_name)
            elif hasattr(app_or_module, "app") and isinstance(
                getattr(app_or_module, "app"), Aiotaskq
            ):
                # Import path points to a module that contains an Aiotaskq instance
                # named as `app` -- retrieve the instance and use it.
                app = getattr(app_or_module, "app")
            else:
                # Import path points to neither an Aiotaskq instance, nor a module
                # containing an Aiotaskq instance.
                tasks = cls._extract_tasks(app_or_module=app_or_module)
                if not tasks:
                    # The Aiotaskq instance or module does not contain any
                    # Task -- Invalid import path.
                    raise AppImportError(app_import_error_msg)
                # The Aiotaskq instance or module contains some Task -- instantiate a
                # new Aiotaskq instance and return it.
                app = cls(tasks=tasks)

        app.import_path = app_or_module_path
        return app

    @classmethod
    def _extract_tasks(cls, app_or_module: "ModuleType") -> list[Task]:
        return [
            getattr(app_or_module, attr)
            for attr in app_or_module.__dict__
            if isinstance(getattr(app_or_module, attr), Task)
        ]
