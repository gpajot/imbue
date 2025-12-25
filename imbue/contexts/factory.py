from typing import Any

from imbue.contexts.abstract import ContextualizedContainer, SyncContextualizedContainer
from imbue.contexts.base import Context, ContextualizedProvider, make_context_decorator

factory_context = make_context_decorator(Context.FACTORY)


class FactoryContainer(ContextualizedContainer):
    CONTEXT = Context.FACTORY

    async def _get_or_provide(self, provider: ContextualizedProvider) -> Any:
        """Always provide."""
        return await self._provide(provider)


class SyncFactoryContainer(SyncContextualizedContainer):
    CONTEXT = Context.FACTORY

    def _get_or_provide(self, provider: ContextualizedProvider) -> Any:
        """Always provide."""
        return self._provide(provider)
