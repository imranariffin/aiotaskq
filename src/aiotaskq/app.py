import importlib
import inspect
import typing as t

from .exceptions import AppImportError
from .task import task, Task, P, RT


class Aiotaskq:
    """Encapsulate the whole application logic."""

    import_path: str
    task_map: dict[str, Task] = {}

    def __init__(self, import_path: t.Optional[str] = None, tasks: t.Optional[list[Task]] = None):
        self.import_path = (
            import_path 
            if import_path is not None 
            else inspect.getmodule(self).__name__  # type: ignore
        )
        self.task_map = {task_.__name__: task_ for task_ in tasks} if tasks else {}

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

        app: "Aiotaskq"
        if ":" in app_or_module_path:
            print("\n0")
            # Import path points to an Aiotaskq instance -- use it.
            module_path, app_name = app_or_module_path.split(":")

            try:
                module = importlib.import_module(module_path)
            except ImportError as exc:
                raise AppImportError(app_import_error_msg) from exc

            app = getattr(module, app_name)
        else:
            try:
                app_or_module = importlib.import_module(f"{app_or_module_path}.aiotaskq")
            except ImportError:
                try:
                    app_or_module = importlib.import_module(app_or_module_path)
                except ImportError as exc:
                    raise AppImportError(app_import_error_msg) from exc

            if isinstance(app_or_module, Aiotaskq):
                # Import path points to an Aiotaskq instance -- use it.
                print("\n1")
                app = app_or_module
            elif hasattr(app_or_module, "app") and isinstance(getattr(app_or_module, "app"), Aiotaskq):
                # Import path points to a module that contains an Aiotaskq instance
                # named as `app` -- retrieve the instance and use it.
                print("\n2")
                app = getattr(app_or_module, "app")
            elif (
                hasattr(app_or_module, "aiotaskq")
                and isinstance(getattr(app_or_module, "aiotaskq"), Aiotaskq)
            ):
                # Import path points to a module that contains an Aiotaskq instance
                # named as `aiotaskq` -- retrieve the instance and use it.
                print("\n3")
                app = getattr(app_or_module, "aiotaskq")
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
                print(f"\n4: {dict((t.__name__, t) for t in tasks)}")
                app = cls(tasks=tasks)

        app.import_path = app_or_module_path
        return app

    def register_task(self, func: t.Callable[P, RT]) -> Task[P, RT]:
        """
        Register a function as a task so that it can be retrieved from an Aiotaskq app instance.
        """
        task_: Task[P, RT] = task(func)
        self.task_map[func.__name__] = task_
        return task_

    @classmethod
    def _extract_tasks(cls, app_or_module: t.Any) -> list[Task]:
        return [
            getattr(app_or_module, attr)
            for attr in app_or_module.__dict__
            if isinstance(getattr(app_or_module, attr), Task)
        ]
