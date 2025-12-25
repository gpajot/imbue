import inspect
from collections.abc import Callable, Iterator
from typing import (
    Any,
    Generic,
    TypeVar,
    get_args,
)

from imbue.dependency import Interfaced, SubDependency
from imbue.providers.abstract import (
    AsyncProviderResult,
    Provided,
    Provider,
    ProviderResult,
    _ProviderResult,
)
from imbue.utils import get_annotations

C = TypeVar("C")


class InstanceProvider(Provider[type[C], C], Generic[C]):
    """Create instances, filling in dependencies."""

    @property
    def sub_dependencies(self) -> Iterator[SubDependency]:
        for name, annotation in get_annotations(
            self.interface.__init__,
            with_return=False,
            with_instance=False,
        ).items():
            yield SubDependency(name, annotation.annotation, annotation.mandatory)

    def get(self, **dependencies: Any) -> ProviderResult[C]:
        return _ProviderResult(self.interface(**dependencies), awaitable=False)


class InterfacedInstanceProvider(Provider[type[C], C], Generic[C]):
    """Create instances, using an interface as the dependency type, filling in dependencies."""

    def __init__(self, dependency: Interfaced[type[C]]):
        super().__init__(dependency.interface)
        self.implementation: type[C] = dependency.implementation

    @property
    def sub_dependencies(self) -> Iterator[SubDependency]:
        for name, annotation in get_annotations(
            self.implementation.__init__,
            with_return=False,
            with_instance=False,
        ).items():
            yield SubDependency(name, annotation.annotation, annotation.mandatory)

    def get(self, **dependencies: Any) -> ProviderResult[C]:
        return _ProviderResult(self.implementation(**dependencies), awaitable=False)


class DelegatedInstanceProvider(Provider[type[C], C], Generic[C]):
    """Create instances, delegating creation to a function."""

    def __init__(
        self,
        provider_func: Callable[..., Provided[C]],
        is_context_manager: bool,
    ):
        self._provider_func = provider_func
        self._awaitable: bool = False
        self.is_context_manager = is_context_manager

        # Get the proper return type and provider func based on different cases.
        # In case it's a generator, wrap in a context manager and get the underlying return type.
        return_annotation: type[C]
        if is_context_manager:
            return_annotation, *_ = get_args(
                get_annotations(provider_func)["return"].annotation
            )
        else:
            return_annotation = get_annotations(provider_func)["return"].annotation
            if inspect.iscoroutinefunction(provider_func):
                self._awaitable = True
        super().__init__(return_annotation)

    @property
    def sub_dependencies(self) -> Iterator[SubDependency]:
        for name, annotation in get_annotations(
            self._provider_func,
            with_return=False,
            with_instance=False,
        ).items():
            yield SubDependency(name, annotation.annotation, annotation.mandatory)

    def get(self, **dependencies: Any) -> AsyncProviderResult[Provided[C]]:
        return _ProviderResult(
            self._provider_func(**dependencies),  # ty: ignore[invalid-argument-type]
            awaitable=self._awaitable,
        )
