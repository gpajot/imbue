from imbue.contexts.abstract import ContextualizedContainer, SyncContextualizedContainer
from imbue.contexts.base import Context, make_context_decorator
from imbue.contexts.factory import FactoryContainer, SyncFactoryContainer

task_context = make_context_decorator(Context.TASK)


class TaskContainer(ContextualizedContainer):
    CONTEXT = Context.TASK

    async def init(self) -> None:
        await super().init()
        # Init the factory container.
        container = FactoryContainer(self._container, self._contextualized)
        self._contextualized[container.CONTEXT] = container
        await self.enter_async_context(container)


class SyncTaskContainer(SyncContextualizedContainer):
    CONTEXT = Context.TASK

    def init(self) -> None:
        super().init()
        # Init the factory container.
        container = SyncFactoryContainer(self._container, self._contextualized)
        self._contextualized[container.CONTEXT] = container
        self.enter_context(container)
