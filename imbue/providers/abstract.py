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
V = TypeVar("V")
A = TypeVar("A", bound=bool)

CMProvided: TypeAlias = AbstractContextManager[V] | AbstractAsyncContextManager[V]
AwaitableProvided: TypeAlias = Awaitable[V]
Provided: TypeAlias = V | CMProvided[V] | AwaitableProvided[V]

P = TypeVar("P", bound=Provided, covariant=True)


@dataclass(frozen=True)
class _ProviderResult(Generic[P, A]):
    provided: P
    awaitable: Final[A]


ProviderResult: TypeAlias = _ProviderResult[V, Literal[False]]
CMProviderResult: TypeAlias = _ProviderResult[CMProvided[V], Literal[False]]
AwaitableProviderResult: TypeAlias = _ProviderResult[
    AwaitableProvided[V], Literal[True]
]
AnyProviderResult: TypeAlias = (
    ProviderResult[V] | CMProviderResult[V] | AwaitableProviderResult[V]
)


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
    def get(self, **dependencies: Any) -> AnyProviderResult[V]:
        """Provide the dependency for the interface."""

    def __repr__(self) -> str:
        return f"{type(self)}(interface={self.interface})"
