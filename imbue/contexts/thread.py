import asyncio
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any, overload

from imbue.abstract import InternalContainer
from imbue.contexts.abstract import (
    ContextualizedContainer,
    SyncContextualizedContainer,
    V,
)
from imbue.contexts.base import Context, make_context_decorator
from imbue.contexts.task import SyncTaskContainer, TaskContainer
from imbue.dependency import Interface

thread_context = make_context_decorator(Context.THREAD)


class ThreadContainer(ContextualizedContainer):
    CONTEXT = Context.THREAD

    def __init__(
        self,
        container: InternalContainer,
        contextualized: dict[Context, "ContextualizedContainer"],
    ):
        super().__init__(container, contextualized)
        self._locks: dict[Interface, AbstractAsyncContextManager] = {}

    @overload
    async def get(self, interface: type[V]) -> V:
        """Specific type annotation for classes."""

    @overload
    async def get(self, interface: Callable) -> Callable:
        """Specific type annotation for functions."""

    async def get(self, interface: Interface) -> Any:
        if provided := self._provided.get(interface):
            return provided
        if interface not in self._locks:
            self._locks[interface] = asyncio.Lock()
        async with self._locks[interface]:
            return await super().get(interface)

    def task_context(self) -> "TaskContainer":
        """Spawn registries for each task."""
        return TaskContainer(self._container, self._contextualized)


class SyncThreadContainer(SyncContextualizedContainer):
    CONTEXT = Context.THREAD

    def task_context(self) -> SyncTaskContainer:
        """Spawn registries for each task."""
        return SyncTaskContainer(self._container, self._contextualized)
