from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from dataclasses import dataclass, field
from unittest.mock import AsyncMock, Mock

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


@dataclass
class CMSyncApplicationDep:
    close: Callable = field(default_factory=Mock)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class CMSyncThreadDep(CMSyncApplicationDep): ...


class CMSyncTaskDep(CMSyncApplicationDep): ...


class CMSyncFactoryDep(CMSyncApplicationDep): ...


@pytest.fixture(scope="session")
def cm_application_package():
    class AppPackage(Package):
        @application_context(eager=True)
        def sync_dep(self, _: InnerAppDep) -> Iterator[CMSyncApplicationDep]:
            with CMSyncApplicationDep() as dep:
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
        def sync_dep(self, _: InnerThreadDep) -> Iterator[CMSyncThreadDep]:
            with CMSyncThreadDep() as dep:
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

        @task_context
        def sync_dep(self) -> Iterator[CMSyncTaskDep]:
            with CMSyncTaskDep() as dep:
                yield dep

    return TaskPackage()


@pytest.fixture(scope="session")
def cm_factory_package():
    class FactoryPackage(Package):
        @factory_context
        async def dep(self) -> AsyncIterator[CMFactoryDep]:
            async with CMFactoryDep() as dep:
                yield dep

        @factory_context
        def sync_dep(self) -> Iterator[CMSyncFactoryDep]:
            with CMSyncFactoryDep() as dep:
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
