from abc import ABC, abstractmethod
from collections.abc import Awaitable, Iterator
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from dataclasses import dataclass
from typing import (
    Any,
    Final,
    Generic,
    Literal,
    TypeAlias,
    TypeVar,
)

from imbue.dependency import SubDependency

T = TypeVar("T")
V = TypeVar("V", covariant=True)
A = TypeVar("A", bound=bool)

Provided: TypeAlias = V | AbstractContextManager[V] | AbstractAsyncContextManager[V]


@dataclass(frozen=True)
class _ProviderResult(Generic[V, A]):
    provided: Final[V | Awaitable[V]]
    awaitable: Final[A]


ProviderResult: TypeAlias = _ProviderResult[V, Literal[False]]
AsyncProviderResult: TypeAlias = _ProviderResult[Awaitable[V], Literal[True]]
AnyProviderResult: TypeAlias = ProviderResult[V] | AsyncProviderResult[V]


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
    def get(self, **dependencies: Any) -> AnyProviderResult[Provided[V]]:
        """Provide the dependency for the interface."""

    def __repr__(self) -> str:
        return f"{type(self)}(interface={self.interface})"
