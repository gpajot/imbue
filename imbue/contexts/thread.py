import asyncio
from typing import Any, AsyncContextManager, Dict

from imbue.abc import InternalContainer
from imbue.contexts.abc import ContextualizedContainer
from imbue.contexts.base import Context, make_context_decorator
from imbue.contexts.task import TaskContainer
from imbue.dependency import Interface

thread_context = make_context_decorator(Context.THREAD)


class ThreadContainer(ContextualizedContainer):
    CONTEXT = Context.THREAD

    def __init__(
        self,
        container: InternalContainer,
        contextualized: Dict[Context, "ContextualizedContainer"],
    ):
        super().__init__(container, contextualized)
        self._locks: Dict[Interface, AsyncContextManager] = {}

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
