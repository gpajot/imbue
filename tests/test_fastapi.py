from dataclasses import dataclass, field
from typing import AsyncIterator, cast

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from typing_extensions import Annotated

from imbue import (
    Container,
    Package,
    auto_context,
    task_context,
)
from imbue.fastapi import Dependency, app_lifespan, request_lifespan


@dataclass
class DepA:
    entered: bool = field(default=False, init=False)
    exited: bool = field(default=False, init=False)


@dataclass
class DepB:
    a: DepA
    entered: bool = field(default=False, init=False)
    exited: bool = field(default=False, init=False)


@pytest.fixture(scope="session")
def container() -> Container:
    class TestPackage(Package):
        @auto_context
        async def a(self) -> AsyncIterator[DepA]:
            dep = DepA()
            dep.entered = True
            yield dep
            dep.exited = True

        @task_context
        async def b(self, a: DepA) -> AsyncIterator[DepB]:
            dep = DepB(a)
            dep.entered = True
            yield dep
            dep.exited = True

    return Container(TestPackage())


@pytest.fixture
def app(container: Container) -> FastAPI:
    return FastAPI(
        lifespan=app_lifespan(container),
        dependencies=[request_lifespan],
    )


def test(app: FastAPI):
    prev_a = prev_b = None

    @app.get("/")
    async def get(
        q: str,
        a: Annotated[DepA, Dependency(DepA)],
        b: Annotated[DepB, Dependency(DepB)],
    ):
        nonlocal prev_a, prev_b
        assert q == "test"
        assert a.entered
        assert not a.exited
        if prev_a is not None:
            assert a is prev_a
        else:
            assert isinstance(a, DepA)
            prev_a = a
        assert b.entered
        assert not b.exited
        if prev_b is not None:
            assert b is not prev_b
            prev_b = b
        else:
            assert isinstance(b, DepB)
            assert b.a is a
            prev_b = b

    with TestClient(app) as client:
        client.get("/", params={"q": "test"})
        assert not cast(DepA, prev_a).exited
        assert cast(DepB, prev_b).exited
        client.get("/", params={"q": "test"})
        assert not cast(DepA, prev_a).exited
        assert cast(DepB, prev_b).exited

    assert cast(DepA, prev_a).exited
