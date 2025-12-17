from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

Interface = type | Callable


@dataclass
class SubDependency:
    """Internally specify sub dependencies."""

    # The name of the dependency argument.
    name: str
    # The external interface of the dependency.
    interface: Interface
    # The dependency is required or optional.
    # If required it will have to be in the container.
    # If optional it will only be provided if in the container.
    # This means that the sub dependency needs a default value provided.
    # This is explicitly not named `optional` to avoid confusion with
    # `Optional` type annotation that means nullable.
    mandatory: bool = True


T = TypeVar("T", bound=Interface)


@dataclass
class Interfaced(Generic[T]):
    """Allows defining dependencies around interfaces.

    The exposed type will be the interface.
    The sub dependencies will the inferred from the implementation.
    The injected dependency will be the instantiated implementation.
    """

    # The external interface of the dependency.
    interface: T
    # The internal implementation of the interface.
    implementation: T


Dependency = Interface | Interfaced
