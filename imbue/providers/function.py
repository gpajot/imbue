from collections.abc import Callable, Iterator
from typing import Any

from imbue.dependency import SubDependency
from imbue.providers.abstract import Provider, ProviderResult, _ProviderResult
from imbue.utils import get_annotations, partial


class FunctionProvider(Provider[Callable, Callable]):
    """Automatically enrich function arguments with dependencies."""

    @property
    def sub_dependencies(self) -> Iterator[SubDependency]:
        for name, annotation in get_annotations(
            self.interface,
            with_return=False,
        ).items():
            # Make all dependencies optional for functions,
            # this will allow to pass other arguments in functions being injected.
            # This will be equivalent to using partial with dependencies already passed.
            yield SubDependency(name, annotation.annotation, mandatory=False)

    def get(self, **dependencies: Any) -> ProviderResult[Callable]:
        return _ProviderResult(partial(self.interface, **dependencies), awaitable=False)


class MethodProvider(Provider[Callable, Callable]):
    """The class is instantiated with dependencies and the bound method is returned."""

    def __init__(self, func: Callable, cls: type):
        super().__init__(func)
        self._cls = cls

    @property
    def sub_dependencies(self) -> Iterator[SubDependency]:
        # The real dependencies are handled in the instance.
        yield SubDependency("__instance__", self._cls)
        for name, annotation in get_annotations(
            self.interface,
            with_return=False,
            with_instance=False,
        ).items():
            # Make all dependencies optional for functions,
            # this will allow to pass other arguments in functions being injected.
            # This will be equivalent to using partial with dependencies already passed.
            yield SubDependency(name, annotation.annotation, mandatory=False)

    def get(self, **dependencies: Any) -> ProviderResult[Callable]:
        instance = dependencies.pop("__instance__")
        return _ProviderResult(
            partial(getattr(instance, self.interface.__name__), **dependencies),  # ty: ignore[unresolved-attribute]
            awaitable=False,
        )
