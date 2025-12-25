from __future__ import annotations

from abc import ABC
from collections.abc import Callable
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    AsyncExitStack,
    ExitStack,
)
from typing import Any, ClassVar, TypeVar, cast, overload

from imbue.abstract import InternalContainer
from imbue.contexts.base import Context, ContextualizedProvider
from imbue.dependency import Interface
from imbue.exceptions import DependencyError
from imbue.providers.instance import DelegatedInstanceProvider

V = TypeVar("V")


class ContextualizedContainer(AsyncExitStack, ABC):
    """Wraps the container to support context handling.
    This will be responsible for storing already provided dependencies for a particular context.
    """

    CONTEXT: ClassVar[Context]

    def __init__(
        self,
        container: InternalContainer,
        contextualized: dict[Context, ContextualizedContainer],
    ):
        super().__init__()
        self._container = container
        self._contextualized = dict(contextualized)
        self._contextualized[self.CONTEXT] = self
        self._provided: dict[Interface, Any] = {}

    @overload
    async def get(self, interface: Callable) -> Callable:
        """Specific type annotation for functions."""

    @overload
    async def get(self, interface: type[V]) -> V:
        """Specific type annotation for classes."""

    async def get(self, interface: Interface) -> Any:
        """Find the proper container based on context and provide."""
        provider = self._container.get_provider(interface)
        return await self._contextualized[
            cast(Context, provider.context)
        ]._get_or_provide(provider)

    async def _get_or_provide(self, provider: ContextualizedProvider) -> Any:
        """Get from already provided or provide the dependency."""
        if provided := self._provided.get(provider.interface):
            return provided
        provided = await self._provide(provider)
        self._provided[provider.interface] = provided
        return provided

    async def _provide(self, provider: ContextualizedProvider) -> Any:
        """Actually provide the dependency."""
        result = provider.get(
            **{
                s.name: await self.get(s.interface)
                for s in self._container.get_sub_dependencies(provider.interface)
            },
        )
        if result.awaitable:
            provided = await result.provided  # ty: ignore[invalid-await]
        else:
            provided = result.provided
        if (
            isinstance(provider.provider, DelegatedInstanceProvider)
            and provider.provider.is_context_manager
        ):
            if isinstance(provided, AbstractAsyncContextManager):
                return await self.enter_async_context(provided)
            if isinstance(provided, AbstractContextManager):
                return self.enter_context(provided)
        return provided

    async def init(self) -> None:
        """Init eager dependencies."""
        for provider in self._container.get_eager_providers(self.CONTEXT):
            await self._get_or_provide(provider)

    async def __aenter__(self):
        await self.init()
        return self

    async def close(self) -> None:
        # No exception here.
        await self.__aexit__(None, None, None)


class SyncContextualizedContainer(ExitStack, ABC):
    """Sync version of ContextualizedContainer."""

    CONTEXT: ClassVar[Context]

    def __init__(
        self,
        container: InternalContainer,
        contextualized: dict[Context, SyncContextualizedContainer],
    ):
        super().__init__()
        self._container = container
        self._contextualized = dict(contextualized)
        self._contextualized[self.CONTEXT] = self
        self._provided: dict[Interface, Any] = {}

    @overload
    def get(self, interface: Callable) -> Callable:
        """Specific type annotation for functions."""

    @overload
    def get(self, interface: type[V]) -> V:
        """Specific type annotation for classes."""

    def get(self, interface: Interface) -> Any:
        """Find the proper container based on context and provide."""
        provider = self._container.get_provider(interface)
        return self._contextualized[cast(Context, provider.context)]._get_or_provide(
            provider
        )

    def _get_or_provide(self, provider: ContextualizedProvider) -> Any:
        """Get from already provided or provide the dependency."""
        if provided := self._provided.get(provider.interface):
            return provided
        provided = self._provide(provider)
        self._provided[provider.interface] = provided
        return provided

    def _provide(self, provider: ContextualizedProvider) -> Any:
        """Actually provide the dependency."""
        result = provider.get(
            **{
                s.name: self.get(s.interface)
                for s in self._container.get_sub_dependencies(provider.interface)
            },
        )
        if result.awaitable:
            raise DependencyError(
                f"async dependency requested in sync context: {provider.provider!r}"
            )
        provided = result.provided
        if (
            isinstance(provider.provider, DelegatedInstanceProvider)
            and provider.provider.is_context_manager
        ):
            if isinstance(provided, AbstractAsyncContextManager):
                raise DependencyError(
                    f"async dependency requested in sync context: {provider.provider!r}"
                )
            if isinstance(provided, AbstractContextManager):
                return self.enter_context(provided)
        return provided

    def init(self) -> None:
        """Init eager dependencies."""
        for provider in self._container.get_eager_providers(self.CONTEXT):
            self._get_or_provide(provider)

    def __enter__(self):
        self.init()
        return self

    def close(self) -> None:
        # No exception here.
        self.__exit__(None, None, None)
