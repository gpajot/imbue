from abc import ABC, abstractmethod
from typing import (
    Any,
    AsyncContextManager,
    ContextManager,
    Generic,
    Iterator,
    TypeVar,
    Union,
)

from imbue.dependency import SubDependency

T = TypeVar("T")
V = TypeVar("V")


class Provider(Generic[T, V], ABC):
    """The foundation of dependency injection.
    The role of the provider is to expose sub dependencies and provide the dependencies given sub dependencies.
    """

    def __init__(self, interface: T):
        self.interface: T = interface

    @property
    @abstractmethod
    def sub_dependencies(self) -> Iterator[SubDependency]:
        """Get the dependencies from the interface."""

    @abstractmethod
    async def get(
        self,
        **dependencies: Any,
    ) -> Union[V, ContextManager[V], AsyncContextManager[V]]:
        """Provide the dependency for the interface."""

    def __repr__(self) -> str:
        return f"{type(self)}(interface={self.interface})"
