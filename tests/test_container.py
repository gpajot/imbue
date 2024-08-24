import pytest

from imbue.container import Container
from imbue.contexts.base import Context, ContextualizedProvider
from imbue.dependency import SubDependency
from imbue.exceptions import DependencyResolutionError
from imbue.package import Package


class TestContainer:
    @pytest.fixture
    def provider_int(self, mocker):
        provider = mocker.Mock(spec=ContextualizedProvider)
        provider.interface = int
        provider.sub_dependencies = iter(())
        provider.context = Context.TASK
        provider.eager = False
        return provider

    @pytest.fixture
    def provider_str(self, mocker):
        provider = mocker.Mock(spec=ContextualizedProvider)
        provider.interface = str
        provider.sub_dependencies = iter([SubDependency("i", int)])
        provider.context = Context.TASK
        provider.eager = False
        return provider

    @pytest.fixture
    def package_int(self, mocker, provider_int):
        package = mocker.Mock(spec=Package)
        package.get_providers.return_value = [provider_int]
        return package

    @pytest.fixture
    def package_str(self, mocker, provider_str):
        package = mocker.Mock(spec=Package)
        package.get_providers.return_value = [provider_str]
        return package

    def test_resolve(self, package_int, package_str):
        registry = Container(package_int, package_str)
        assert int in registry._providers
        assert str in registry._providers

    def test_resolve_circular(self, provider_int, package_int):
        provider_int.sub_dependencies = iter([SubDependency("i", int)])
        with pytest.raises(
            DependencyResolutionError,
            match="circular dependency found",
        ):
            Container(package_int)

    def test_resolve_not_found(self, package_str):
        with pytest.raises(DependencyResolutionError, match="no provider found"):
            Container(package_str)

    def test_resolve_duplicate(self, package_int):
        with pytest.raises(DependencyResolutionError, match="multiple providers found"):
            Container(package_int, package_int)

    def test_resolve_check_contexts_ko(self, provider_str, package_int, package_str):
        provider_str.context = Context.APPLICATION
        with pytest.raises(DependencyResolutionError, match="context error"):
            Container(package_int, package_str)

    def test_resolve_check_contexts_ok(self, provider_int, package_int, package_str):
        provider_int.context = Context.APPLICATION
        Container(package_int, package_str)

    def test_resolve_check_contexts_auto_with_deps(
        self,
        provider_str,
        package_int,
        package_str,
    ):
        provider_str.context = None
        Container(package_int, package_str)
        assert provider_str.context == Context.TASK

    def test_resolve_check_contexts_auto_all(
        self,
        provider_int,
        provider_str,
        package_int,
        package_str,
    ):
        provider_int.context = None
        provider_str.context = None
        Container(package_int, package_str)
        assert provider_int.context == Context.APPLICATION
        assert provider_str.context == Context.APPLICATION
