from dataclasses import dataclass

import pytest

from imbue.container import Container
from imbue.contexts.base import Context
from tests.conftest import StandaloneDep


@dataclass
class Tasks:
    standalone: StandaloneDep

    def a(self, arg: bool) -> tuple["Tasks", bool]:
        return self, arg

    def b(self, arg: bool) -> tuple["Tasks", bool]:
        return self, arg


def func(standalone: StandaloneDep, arg: bool) -> tuple[StandaloneDep, bool]:
    return standalone, arg


@pytest.fixture
def container():
    container = Container()
    container.add(StandaloneDep, context=Context.APPLICATION)
    container.add(Tasks.a)
    container.add(Tasks.b)
    container.add(func)
    return container


async def test_tasks_can_be_added_and_injected(container):
    async with container.application_context() as app_container:
        async with app_container.task_context() as req_container:
            standalone = await req_container.get(StandaloneDep)
            instance_a, arg_a = (await req_container.get(Tasks.a))(arg=True)
            assert arg_a is True
            instance_b, arg_b = (await req_container.get(Tasks.b))(arg=True)
            assert arg_b is True
            assert instance_a is instance_b
            assert isinstance(instance_a, Tasks)
            assert instance_a.standalone is standalone
            standalone_func, arg_func = (await req_container.get(func))(arg=True)
            assert standalone_func is standalone
            assert arg_func is True
