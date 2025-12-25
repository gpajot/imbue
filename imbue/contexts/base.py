from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    asynccontextmanager,
    contextmanager,
)
from dataclasses import dataclass
from enum import IntEnum
from typing import (
    Any,
    Generic,
    TypeVar,
)

from imbue.dependency import Dependency, SubDependency
from imbue.providers.abstract import AnyProviderResult, Provided, Provider
from imbue.providers.common import get_providers
from imbue.providers.instance import DelegatedInstanceProvider
from imbue.utils import partial


class Context(IntEnum):
    """Supported contexts, lower have longer lifetime."""

    APPLICATION = 10  # Equivalent to singletons.
    THREAD = 20
    TASK = 30
    FACTORY = 40  # Never reused.


T = TypeVar("T")
V = TypeVar("V")


@dataclass
class ContextualizedDependency:
    dependency: Dependency
    context: Context | None = None
    eager: bool = False

    def get_providers(self) -> Iterator[ContextualizedProvider]:
        yield from ContextualizedProvider.from_dependency(
            self.dependency,
            self.context,
            self.eager,
        )


@dataclass
class ContextualizedProvider(Generic[T, V]):
    """Wrap a provider to handle context and lifetime."""

    provider: Provider[T, V]
    context: Context | None
    eager: bool

    @classmethod
    def from_dependency(
        cls,
        dependency: Dependency,
        context: Context | None = None,
        eager: bool = False,
    ) -> Iterator[ContextualizedProvider]:
        """In some cases, an interface yields multiple providers.
        Ex: a method yields a provider for a class and one for the method.
        """
        for provider in get_providers(dependency):
            yield cls(
                provider=provider,
                context=context,
                eager=eager,
            )

    @property
    def interface(self) -> T:
        return self.provider.interface

    @property
    def sub_dependencies(self) -> Iterator[SubDependency]:
        yield from self.provider.sub_dependencies

    def get(self, **dependencies: Any) -> AnyProviderResult[Provided[V]]:
        return self.provider.get(**dependencies)


@dataclass
class DelegatedProviderWrapper(Generic[V]):
    """Wrapper for delegated provider methods.
    Its purpose is to wait until we have an instance to pass to the method.
    """

    func: Callable[..., V | Iterator[V] | AsyncIterator[V]]
    context: Context | None
    eager: bool

    def to_contextualized_provider(
        self,
        instance: Any,
    ) -> ContextualizedProvider[type[V], V]:
        """Get the provider from this wrapper."""
        func, is_context_manager = self._get_func()
        return ContextualizedProvider(
            provider=DelegatedInstanceProvider(
                provider_func=partial(func, self=instance),
                is_context_manager=is_context_manager,
            ),
            context=self.context,
            eager=self.eager,
        )

    def _get_func(
        self,
    ) -> tuple[
        Callable[
            ...,
            V | AbstractContextManager[V] | AbstractAsyncContextManager[V],
        ],
        bool,
    ]:
        """Support for context managers."""
        if inspect.isasyncgenfunction(self.func):
            return asynccontextmanager(self.func), True  # ty: ignore[invalid-argument-type]
        if inspect.isgeneratorfunction(self.func):
            return contextmanager(self.func), True  # ty: ignore[invalid-argument-type]
        return self.func, False  # ty: ignore[invalid-return-type]


def make_context_decorator(context: Context | None):
    """Wrap a delegated function providing an interface to assign a context and handle eagerness."""

    def _wrapper(func: Callable | None = None, *, eager: bool = False):
        def wrap(fn: Callable) -> DelegatedProviderWrapper:
            return DelegatedProviderWrapper(func=fn, context=context, eager=eager)

        # Check if called like `@context` or `@context()`.
        if func is None:
            # Called with parentheses.
            return wrap
        # Called without parentheses.
        return wrap(func)

    return _wrapper


auto_context = make_context_decorator(None)
