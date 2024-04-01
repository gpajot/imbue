from dataclasses import dataclass, field
from typing import AsyncIterator, Awaitable, Callable
from unittest.mock import AsyncMock

import pytest

from imbue.container import Container
from imbue.contexts.application import application_context
from imbue.contexts.factory import factory_context
from imbue.contexts.task import task_context
from imbue.contexts.thread import thread_context
from imbue.package import Package


class InnerAppDep: ...


class InnerThreadDep: ...


@dataclass
class CMApplicationDep:
    close: Callable[..., Awaitable] = field(default_factory=AsyncMock)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class CMThreadDep(CMApplicationDep): ...


class CMTaskDep(CMApplicationDep): ...


class CMFactoryDep(CMApplicationDep): ...


@pytest.fixture(scope="session")
def cm_application_package():
    class AppPackage(Package):
        @application_context(eager=True)
        async def dep(self, _: InnerAppDep) -> AsyncIterator[CMApplicationDep]:
            async with CMApplicationDep() as dep:
                yield dep

        @application_context
        def inner(self) -> InnerAppDep:
            return InnerAppDep()

    return AppPackage()


@pytest.fixture(scope="session")
def cm_thread_package():
    class ThreadPackage(Package):
        @thread_context
        async def dep(self, _: InnerThreadDep) -> AsyncIterator[CMThreadDep]:
            async with CMThreadDep() as dep:
                yield dep

        @thread_context
        def inner(self) -> InnerThreadDep:
            return InnerThreadDep()

    return ThreadPackage()


@pytest.fixture(scope="session")
def cm_task_package():
    class TaskPackage(Package):
        @task_context
        async def dep(self) -> AsyncIterator[CMTaskDep]:
            async with CMTaskDep() as dep:
                yield dep

    return TaskPackage()


@pytest.fixture(scope="session")
def cm_factory_package():
    class FactoryPackage(Package):
        @factory_context
        async def dep(self) -> AsyncIterator[CMFactoryDep]:
            async with CMFactoryDep() as dep:
                yield dep

    return FactoryPackage()


@pytest.fixture(scope="session")
def container(
    cm_application_package,
    cm_thread_package,
    cm_task_package,
    cm_factory_package,
):
    return Container(
        cm_application_package,
        cm_thread_package,
        cm_task_package,
        cm_factory_package,
    )


@pytest.fixture()
def application_container(container):
    return container.application_context()


@pytest.fixture()
async def thread_container(application_container):
    async with application_container:
        yield application_container.thread_context()


@pytest.fixture()
async def task_container(application_container):
    async with application_container:
        yield application_container.task_context()
