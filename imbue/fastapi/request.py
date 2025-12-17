from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi.params import Depends
from fastapi.requests import HTTPConnection

from imbue.contexts.task import TaskContainer
from imbue.dependency import Interface


async def _task_container(connection: HTTPConnection) -> AsyncIterator[TaskContainer]:
    """Initialize the task container.
    This needs to be done for every request.
    For more details, see:
        - https://fastapi.tiangolo.com/tutorial/dependencies/global-dependencies/
        - https://fastapi.tiangolo.com/tutorial/dependencies/
    """
    async with connection.state.app_container.task_context() as container:
        yield container


request_lifespan = Depends(_task_container, use_cache=True)


class Dependency(Depends):
    def __init__(self, interface: Interface):
        async def _get(container: Annotated[TaskContainer, request_lifespan]) -> Any:
            return await container.get(interface)

        super().__init__(_get, use_cache=False)
