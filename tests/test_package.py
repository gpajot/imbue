import pytest

from imbue.contexts.base import (
    Context,
    ContextualizedDependency,
    ContextualizedProvider,
)
from imbue.contexts.thread import thread_context
from imbue.package import Package
from tests.conftest import StandaloneDep, async_func


class TestPackage:
    @pytest.fixture()
    def package(self):
        class TheTestPackage(Package):
            EXTRA_DEPENDENCIES = [ContextualizedDependency(async_func, Context.THREAD)]

            @thread_context
            def provide_method(self) -> StandaloneDep:
                assert isinstance(self, TheTestPackage)
                return StandaloneDep()

        return TheTestPackage()

    async def test_get_providers(self, package):
        providers = list(package.get_providers())
        assert len(providers) == 2
        for provider in providers:
            assert isinstance(provider, ContextualizedProvider)
            assert provider.context is Context.THREAD
