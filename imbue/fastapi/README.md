# FastAPI integration

This integration connects imbue dependency injection to FastAPI's own system.

To use this library with FastAPI,
some setup is needed when instantiating the app,
then simply wrap dependency types with `Dependency` as you would with `fastapi.Depends`:

```python
from typing import Annotated
from fastapi import FastAPI
from imbue import Container
from imbue.fastapi import app_lifespan, request_lifespan, Dependency

from myapp import DepA, DepB


container: Container = ...

app = FastAPI(
    lifespan=app_lifespan(container),
    dependencies=[request_lifespan],
)


@app.get("/")
async def get(
    a: Annotated[DepA, Dependency(DepA)],
    b: Annotated[DepB, Dependency(DepB)],
): ...
```