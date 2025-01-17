from imbue.contexts.abstract import ContextualizedContainer
from imbue.contexts.base import Context, make_context_decorator
from imbue.contexts.factory import FactoryContainer

task_context = make_context_decorator(Context.TASK)


class TaskContainer(ContextualizedContainer):
    CONTEXT = Context.TASK

    async def init(self) -> None:
        await super().init()
        # Init the factory container.
        container = FactoryContainer(self._container, self._contextualized)
        self._contextualized[container.CONTEXT] = container
        await self.enter_async_context(container)
