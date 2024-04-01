import asyncio
import contextlib

from tests.contexts.conftest import (
    CMApplicationDep,
    CMFactoryDep,
    CMTaskDep,
    CMThreadDep,
)


class TestRegistry:
    async def test_cm_lifecycle(self, container):
        async with container.application_context() as app_container:
            app_dep = await app_container.get(CMApplicationDep)
            main_thread_dep = await app_container.get(CMThreadDep)
            async with app_container.thread_context() as thread_container:
                thread_dep = await thread_container.get(CMThreadDep)
                async with thread_container.task_context() as task_container:
                    task_dep = await task_container.get(CMTaskDep)
                    task_dep.close.assert_not_called()
                    fact_dep = await task_container.get(CMFactoryDep)
                    fact_dep.close.assert_not_called()
                fact_dep.close.assert_awaited_once()
                task_dep.close.assert_awaited_once()
                thread_dep.close.assert_not_called()
            thread_dep.close.assert_awaited_once()
            app_dep.close.assert_not_called()
            main_thread_dep.close.assert_not_called()
        app_dep.close.assert_awaited_once()
        main_thread_dep.close.assert_awaited_once()

    async def test_same_context_should_yield_same_dependency(self, container):
        async with container.application_context() as app_container:
            assert await app_container.get(
                CMApplicationDep,
            ) is await app_container.get(CMApplicationDep)
            assert await app_container.get(CMThreadDep) is await app_container.get(
                CMThreadDep,
            )
            async with app_container.thread_context() as thread_container:
                assert await thread_container.get(
                    CMThreadDep,
                ) is await thread_container.get(CMThreadDep)
                async with thread_container.task_context() as task_container:
                    assert await task_container.get(
                        CMTaskDep,
                    ) is await task_container.get(CMTaskDep)

    async def test_different_contexts_should_yield_different_dependencies(
        self,
        application_container,
    ):
        async with application_container:

            async def get_dep():
                async with application_container.task_context() as task_container:
                    return await task_container.get(CMTaskDep)

            dep1, dep2 = await asyncio.gather(get_dep(), get_dep())
            assert dep1 is not dep2

    async def test_error_handling(self, application_container):
        with contextlib.suppress(ValueError):
            async with application_container:
                dep = await application_container.get(CMApplicationDep)
                raise ValueError("...")
        dep.close.assert_awaited_once()
