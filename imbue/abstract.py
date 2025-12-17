from abc import ABC, abstractmethod
from collections.abc import Iterator

from imbue.contexts.base import Context, ContextualizedProvider
from imbue.dependency import Interface, SubDependency


class InternalContainer(ABC):
    """Internal abstract to define an interface to a container to other parts of the injection system."""

    @abstractmethod
    def get_provider(self, interface: Interface) -> ContextualizedProvider:
        """Get a provider for an interface."""

    @abstractmethod
    def get_sub_dependencies(self, interface: Interface) -> Iterator[SubDependency]:
        """Get all dependencies from a provider."""

    @abstractmethod
    def get_eager_providers(self, context: Context) -> Iterator[ContextualizedProvider]:
        """Get all eager providers for a context."""
