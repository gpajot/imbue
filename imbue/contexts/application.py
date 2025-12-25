import threading
from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, overload

from imbue.abstract import InternalContainer
from imbue.contexts.abstract import (
    ContextualizedContainer,
    SyncContextualizedContainer,
    V,
)
from imbue.contexts.base import Context, make_context_decorator
from imbue.contexts.task import SyncTaskContainer, TaskContainer
from imbue.contexts.thread import SyncThreadContainer, ThreadContainer
from imbue.dependency import Interface

application_context = make_context_decorator(Context.APPLICATION)


class ApplicationContainer(ContextualizedContainer):
    CONTEXT = Context.APPLICATION

    def __init__(
        self,
        container: InternalContainer,
        contextualized: dict[Context, "ContextualizedContainer"],
    ):
        super().__init__(container, contextualized)
        self._lock = threading.RLock()
        self._locks: dict[Interface, AbstractContextManager] = {}

    async def init(self) -> None:
        await super().init()
        # Init the main thread's container.
        container = ThreadContainer(self._container, self._contextualized)
        self._contextualized[container.CONTEXT] = container
        await self.enter_async_context(container)

    @overload
    async def get(self, interface: type[V]) -> V:
        """Specific type annotation for classes."""

    @overload
    async def get(self, interface: Callable) -> Callable:
        """Specific type annotation for functions."""

    async def get(self, interface: Interface) -> Any:
        if provided := self._provided.get(interface):
            return provided
        with self._lock:
            if interface not in self._locks:
                self._locks[interface] = threading.Lock()
        with self._locks[interface]:
            return await super().get(interface)

    def thread_context(self) -> "ThreadContainer":
        """Spawn registries for other thread."""
        return ThreadContainer(self._container, self._contextualized)

    def task_context(self) -> "TaskContainer":
        """Spawn registries for each task."""
        return TaskContainer(self._container, self._contextualized)


class SyncApplicationContainer(SyncContextualizedContainer):
    CONTEXT = Context.APPLICATION

    def __init__(
        self,
        container: InternalContainer,
        contextualized: dict[Context, "SyncContextualizedContainer"],
    ):
        super().__init__(container, contextualized)
        self._lock = threading.RLock()
        self._locks: dict[Interface, AbstractContextManager] = {}

    def init(self) -> None:
        super().init()
        # Init the main thread's container.
        container = SyncThreadContainer(self._container, self._contextualized)
        self._contextualized[container.CONTEXT] = container
        self.enter_context(container)

    @overload
    def get(self, interface: type[V]) -> V:
        """Specific type annotation for classes."""

    @overload
    def get(self, interface: Callable) -> Callable:
        """Specific type annotation for functions."""

    def get(self, interface: Interface) -> Any:
        if provided := self._provided.get(interface):
            return provided
        with self._lock:
            if interface not in self._locks:
                self._locks[interface] = threading.Lock()
        with self._locks[interface]:
            return super().get(interface)

    def thread_context(self) -> "SyncThreadContainer":
        """Spawn registries for other thread."""
        return SyncThreadContainer(self._container, self._contextualized)

    def task_context(self) -> "SyncTaskContainer":
        """Spawn registries for each task."""
        return SyncTaskContainer(self._container, self._contextualized)
