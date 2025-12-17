import inspect
from collections.abc import Iterable, Iterator
from typing import ClassVar

from imbue.contexts.base import (
    ContextualizedDependency,
    ContextualizedProvider,
    DelegatedProviderWrapper,
)
from imbue.dependency import Dependency


class Package:
    """Container class to group dependency providers.
    Each dependency is provided by a method.
    Additionally, you can specify dependencies for which no
    provider function is required in `EXTRA_DEPENDENCIES`.
    """

    EXTRA_DEPENDENCIES: ClassVar[Iterable[Dependency | ContextualizedDependency]] = ()

    def get_providers(self) -> Iterator[ContextualizedProvider]:
        for dependency in self.EXTRA_DEPENDENCIES:
            if isinstance(dependency, ContextualizedDependency):
                yield from dependency.get_providers()
            else:
                yield from ContextualizedProvider.from_dependency(dependency)
        for _, member in inspect.getmembers(self):
            if not isinstance(member, DelegatedProviderWrapper):
                continue
            # Now that we have an instance to bind, we can get the final provider.
            yield member.to_contextualized_provider(instance=self)
