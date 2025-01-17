import threading
from typing import Any, Callable, ContextManager, Dict, Type, overload

from imbue.abstract import InternalContainer
from imbue.contexts.abstract import ContextualizedContainer, V
from imbue.contexts.base import Context, make_context_decorator
from imbue.contexts.task import TaskContainer
from imbue.contexts.thread import ThreadContainer
from imbue.dependency import Interface

application_context = make_context_decorator(Context.APPLICATION)


class ApplicationContainer(ContextualizedContainer):
    CONTEXT = Context.APPLICATION

    def __init__(
        self,
        container: InternalContainer,
        contextualized: Dict[Context, "ContextualizedContainer"],
    ):
        super().__init__(container, contextualized)
        self._lock = threading.RLock()
        self._locks: Dict[Interface, ContextManager] = {}

    async def init(self) -> None:
        await super().init()
        # Init the main thread's container.
        container = ThreadContainer(self._container, self._contextualized)
        self._contextualized[container.CONTEXT] = container
        await self.enter_async_context(container)

    @overload
    async def get(self, interface: Callable) -> Callable:
        """Specific type annotation for functions."""

    @overload
    async def get(self, interface: Type[V]) -> V:
        """Specific type annotation for classes."""

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
