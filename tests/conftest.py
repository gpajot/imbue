from abc import ABC
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass

import pytest

from imbue.dependency import Interfaced
from imbue.providers.function import (
    FunctionProvider,
    MethodProvider,
)
from imbue.providers.instance import (
    DelegatedInstanceProvider,
    InstanceProvider,
    InterfacedInstanceProvider,
)

# Dependencies.


class StandaloneDep: ...


@dataclass
class NestedDep:
    standalone: StandaloneDep


class InterfaceDep(ABC): ...  # noqa:B024


@dataclass
class ImplementationDep(InterfaceDep):
    standalone: StandaloneDep


@dataclass
class Tasks:
    standalone: StandaloneDep

    def blocking_meth(self, arg: bool) -> tuple[StandaloneDep, bool]:
        return self.standalone, arg

    async def async_meth(self, arg: bool) -> tuple[StandaloneDep, bool]:
        return self.standalone, arg


def blocking_func(standalone: StandaloneDep, arg: bool) -> tuple[StandaloneDep, bool]:
    return standalone, arg


async def async_func(
    standalone: StandaloneDep,
    arg: bool,
) -> tuple[StandaloneDep, bool]:
    return standalone, arg


# Providers.


@pytest.fixture
def standalone_provider():
    return InstanceProvider(StandaloneDep)


@pytest.fixture
def nested_provider():
    return InstanceProvider(NestedDep)


@pytest.fixture
def interfaced_instance_provider():
    return InterfacedInstanceProvider(Interfaced(InterfaceDep, ImplementationDep))


@pytest.fixture
def nested_generator_provider():
    def func(standalone: StandaloneDep) -> Iterator[NestedDep]:
        try:
            yield NestedDep(standalone)
        finally:
            pass

    return DelegatedInstanceProvider(contextmanager(func), True)


@pytest.fixture
def nested_async_generator_provider():
    async def func(standalone: StandaloneDep) -> AsyncIterator[NestedDep]:
        try:
            yield NestedDep(standalone)
        finally:
            pass

    return DelegatedInstanceProvider(asynccontextmanager(func), True)


@pytest.fixture
def nested_function_provider():
    def func(standalone: StandaloneDep) -> NestedDep:
        return NestedDep(standalone)

    return DelegatedInstanceProvider(func, False)


@pytest.fixture
def nested_async_function_provider():
    async def func(standalone: StandaloneDep) -> NestedDep:
        return NestedDep(standalone)

    return DelegatedInstanceProvider(func, False)


@pytest.fixture
def tasks_provider():
    return InstanceProvider(Tasks)


@pytest.fixture
def async_meth_provider():
    return MethodProvider(Tasks.async_meth, Tasks)


@pytest.fixture
def blocking_meth_provider():
    return MethodProvider(Tasks.blocking_meth, Tasks)


@pytest.fixture
def async_func_provider():
    return FunctionProvider(async_func)


@pytest.fixture
def blocking_func_provider():
    return FunctionProvider(blocking_func)
