from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterator, List, Union

from imbue.abc import InternalContainer
from imbue.contexts.application import ApplicationContainer
from imbue.contexts.base import (
    Context,
    ContextualizedDependency,
    ContextualizedProvider,
)
from imbue.dependency import Dependency, Interface, SubDependency
from imbue.exceptions import DependencyResolutionError
from imbue.package import Package


@dataclass
class DependencyChain:
    """Dependency chain, representing the graph of dependencies.
    Its role is to check whether there are no cycles nor context issues.
    """

    chain: List[ContextualizedProvider]

    def add(self, provider: ContextualizedProvider) -> "DependencyChain":
        """Create a new chain, adding the provider at the end."""
        chain = DependencyChain([*self.chain, provider])
        # Check for cycles.
        if provider in self.chain:
            raise DependencyResolutionError(f"circular dependency found:\n{chain}")
        # The deeper the chain, the lower the context must be.
        # App dependencies cannot have task dependencies but the inverse is possible.
        if provider.context > self.last.context:
            raise DependencyResolutionError(f"context error:\n{chain}")
        return chain

    @property
    def last(self) -> ContextualizedProvider:
        """Get the last provider in the chain."""
        return self.chain[-1]

    def __str__(self) -> str:
        return "\n".join(
            (
                f"{' ' * i}-> {p.interface} ({p.context})"
                for i, p in enumerate(self.chain)
            ),
        )


class Container(InternalContainer):
    def __init__(
        self,
        *dependencies_or_packages: Union[Dependency, ContextualizedDependency, Package],
        default_dependency_context: Context = Context.TASK,
    ):
        # The link between an interface and its provider.
        self._providers: Dict[Interface, ContextualizedProvider] = {}
        # Cache sub dependencies for each interface.
        self._sub_dependencies: Dict[Interface, List[SubDependency]] = {}
        # All providers that should be eager inited.
        self._by_context_eager_providers: Dict[
            Context, List[ContextualizedProvider]
        ] = defaultdict(
            list,
        )

        # Add all dependencies.
        for dep_or_pkg in dependencies_or_packages:
            if isinstance(dep_or_pkg, (ContextualizedDependency, Package)):
                providers_iterator = dep_or_pkg.get_providers()
            else:
                providers_iterator = ContextualizedProvider.from_dependency(
                    dep_or_pkg, default_dependency_context
                )
            for provider in providers_iterator:
                if provider.interface in self._providers:
                    raise DependencyResolutionError(
                        "multiple providers found for the same type: "
                        f"{self._providers[provider.interface]!r}, {provider!r}",
                    )
                self._providers[provider.interface] = provider
        # Resolve the graph.
        for provider in self._providers.values():
            self._resolve(DependencyChain([provider]))

    def _resolve(self, chain: DependencyChain) -> None:
        """Construct the graph of sub dependencies."""
        provider = chain.last
        if provider.interface in self._sub_dependencies:
            # Already handled.
            return
        dependencies: List[SubDependency] = []
        for sub_dependency in provider.sub_dependencies:
            if (
                not sub_dependency.mandatory
                and sub_dependency.interface not in self._providers
            ):
                continue
            if sub_dependency.interface not in self._providers:
                raise DependencyResolutionError(
                    f"no provider found for {sub_dependency.interface}, from provider {provider!r}",
                )
            sub_provider = self._providers[sub_dependency.interface]
            self._resolve(chain.add(sub_provider))
            dependencies.append(sub_dependency)
        self._sub_dependencies[provider.interface] = dependencies
        if provider.eager:
            self._by_context_eager_providers[provider.context].append(provider)

    def add(self, dependency: Dependency, context: Context = Context.TASK) -> None:
        """Add another interface, used to eagerly add all task functions/methods as providers.
        This allows to make all necessary checks at application start rather than during task processing.
        """
        for provider in ContextualizedProvider.from_dependency(
            dependency=dependency,
            context=context,
        ):
            if provider.interface in self._providers:
                continue
            self._providers[provider.interface] = provider
            self._resolve(DependencyChain([provider]))

    def get_provider(self, interface: Interface) -> ContextualizedProvider:
        """Get the provider for an interface."""
        if interface not in self._providers:
            raise DependencyResolutionError(f"unknow interface {interface}")
        return self._providers[interface]

    def get_sub_dependencies(self, interface: Interface) -> Iterator[SubDependency]:
        """Get all sub dependencies for an interface."""
        yield from self._sub_dependencies[interface]

    def get_eager_providers(self, context: Context) -> Iterator[ContextualizedProvider]:
        """Get all providers that should be eager inited for a context."""
        return iter(self._by_context_eager_providers[context])

    def application_context(self) -> "ApplicationContainer":
        """Spawns the first contextualized container on the application level."""
        return ApplicationContainer(self, {})
