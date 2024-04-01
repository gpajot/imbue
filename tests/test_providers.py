import pytest

from imbue.dependency import SubDependency
from tests.conftest import (
    ImplementationDep,
    InterfaceDep,
    NestedDep,
    StandaloneDep,
    Tasks,
    async_func,
    blocking_func,
)


class TestProviders:
    @pytest.mark.parametrize(
        ("provider", "interface"),
        [
            ("standalone_provider", StandaloneDep),
            ("nested_provider", NestedDep),
            ("interfaced_instance_provider", InterfaceDep),
            ("nested_generator_provider", NestedDep),
            ("nested_async_generator_provider", NestedDep),
            ("nested_function_provider", NestedDep),
            ("nested_async_function_provider", NestedDep),
            ("async_func_provider", async_func),
            ("blocking_func_provider", blocking_func),
            ("async_meth_provider", Tasks.async_meth),
            ("blocking_meth_provider", Tasks.blocking_meth),
        ],
    )
    def test_interface(self, provider, interface, request):
        assert request.getfixturevalue(provider).interface == interface

    @pytest.mark.parametrize(
        ("provider", "dependencies"),
        [
            ("standalone_provider", []),
            ("nested_provider", [SubDependency("standalone", StandaloneDep)]),
            (
                "interfaced_instance_provider",
                [SubDependency("standalone", StandaloneDep)],
            ),
            ("nested_generator_provider", [SubDependency("standalone", StandaloneDep)]),
            (
                "nested_async_generator_provider",
                [SubDependency("standalone", StandaloneDep)],
            ),
            ("nested_function_provider", [SubDependency("standalone", StandaloneDep)]),
            (
                "nested_async_function_provider",
                [SubDependency("standalone", StandaloneDep)],
            ),
            (
                "async_func_provider",
                [
                    SubDependency("standalone", StandaloneDep, mandatory=False),
                    SubDependency("arg", bool, mandatory=False),
                ],
            ),
            (
                "blocking_func_provider",
                [
                    SubDependency("standalone", StandaloneDep, mandatory=False),
                    SubDependency("arg", bool, mandatory=False),
                ],
            ),
            (
                "async_meth_provider",
                [
                    SubDependency("__instance__", Tasks),
                    SubDependency("arg", bool, mandatory=False),
                ],
            ),
            (
                "blocking_meth_provider",
                [
                    SubDependency("__instance__", Tasks),
                    SubDependency("arg", bool, mandatory=False),
                ],
            ),
        ],
    )
    def test_sub_dependencies(self, provider, dependencies, request):
        assert list(request.getfixturevalue(provider).sub_dependencies) == dependencies

    async def test_get_nested_instance(self, nested_provider):
        standalone = StandaloneDep()
        provided = await nested_provider.get(standalone=standalone)
        assert isinstance(provided, NestedDep)
        assert provided.standalone is standalone

    async def test_get_interfaced_instance(self, interfaced_instance_provider):
        standalone = StandaloneDep()
        provided = await interfaced_instance_provider.get(standalone=standalone)
        assert isinstance(provided, ImplementationDep)
        assert provided.standalone is standalone

    async def test_get_nested_generator(self, nested_generator_provider):
        standalone = StandaloneDep()
        cm = await nested_generator_provider.get(standalone=standalone)
        with cm as provided:
            assert isinstance(provided, NestedDep)
            assert provided.standalone is standalone

    async def test_get_nested_async_generator(self, nested_async_generator_provider):
        standalone = StandaloneDep()
        cm = await nested_async_generator_provider.get(standalone=standalone)
        async with cm as provided:
            assert isinstance(provided, NestedDep)
            assert provided.standalone is standalone

    async def test_get_nested_function(self, nested_function_provider):
        standalone = StandaloneDep()
        provided = await nested_function_provider.get(standalone=standalone)
        assert isinstance(provided, NestedDep)
        assert provided.standalone is standalone

    async def test_get_nested_async_function(self, nested_async_function_provider):
        standalone = StandaloneDep()
        provided = await nested_async_function_provider.get(standalone=standalone)
        assert isinstance(provided, NestedDep)
        assert provided.standalone is standalone

    async def test_get_async_func(self, async_func_provider):
        standalone = StandaloneDep()
        output, arg = await (await async_func_provider.get(standalone=standalone))(
            arg=True,
        )
        assert output is standalone
        assert arg is True

    async def test_get_blocking_func(self, blocking_func_provider):
        standalone = StandaloneDep()
        output, arg = (await blocking_func_provider.get(standalone=standalone))(
            arg=True,
        )
        assert output is standalone
        assert arg is True

    async def test_get_async_meth(self, async_meth_provider, tasks_provider):
        standalone = StandaloneDep()
        endpoints = await tasks_provider.get(standalone=standalone)
        output, arg = await (await async_meth_provider.get(__instance__=endpoints))(
            arg=True,
        )
        assert output is standalone
        assert arg is True

    async def test_get_blocking_meth(self, blocking_meth_provider, tasks_provider):
        standalone = StandaloneDep()
        endpoints = await tasks_provider.get(standalone=standalone)
        output, arg = (await blocking_meth_provider.get(__instance__=endpoints))(
            arg=True,
        )
        assert output is standalone
        assert arg is True
