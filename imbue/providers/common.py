import inspect
from typing import Iterator

from imbue.dependency import Dependency, Interfaced
from imbue.exceptions import UnsupportedDependencyInterfaceError
from imbue.providers.abstract import Provider
from imbue.providers.function import (
    FunctionProvider,
    MethodProvider,
)
from imbue.providers.instance import (
    InstanceProvider,
    InterfacedInstanceProvider,
)


def get_providers(dependency: Dependency) -> Iterator[Provider]:
    """Get the providers or raise if incorect type."""
    if isinstance(dependency, Interfaced):
        yield InterfacedInstanceProvider(dependency)
    elif inspect.isclass(dependency):
        yield InstanceProvider(dependency)
    elif inspect.iscoroutinefunction(dependency) or inspect.isfunction(dependency):
        # Determine if it's a method of function.
        func_names = dependency.__qualname__.split(".")
        if len(func_names) == 2:
            cls = getattr(
                inspect.getmodule(dependency),
                func_names[0],
                None,
            )
            if cls is None:
                raise UnsupportedDependencyInterfaceError(
                    f"could not find class for function {dependency!r}",
                )
            # Also yield the instance provider.
            yield InstanceProvider(cls)
            yield MethodProvider(dependency, cls)
        elif len(func_names) == 1:
            yield FunctionProvider(dependency)
        else:
            raise UnsupportedDependencyInterfaceError(
                f"{dependency!r} has too many parts in qualname",
            )
    else:
        raise UnsupportedDependencyInterfaceError(
            f"{dependency!r} must be a class, function or method",
        )
