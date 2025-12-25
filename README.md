# imbue

[![tests](https://github.com/gpajot/imbue/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/gpajot/imbue/actions/workflows/test.yml?query=branch%3Amain+event%3Apush)
[![PyPi](https://img.shields.io/pypi/v/imbue?label=stable)](https://pypi.org/project/imbue/)
[![python](https://img.shields.io/pypi/pyversions/imbue)](https://pypi.org/project/imbue/)

Type based python dependency injection framework.

## Why another dependency injection library?

There are many out there, including some that comes directly with (web) frameworks.
I wanted one that was explicitly contextualized
in the different layers of the application and that did not leak in the domain layer.
In many cases, dependencies are simply parameters that are passed to constructors,
and ideally, the domain layer should not know anything how they are injected.

## Main objects
- `Container`: a singleton containing all dependencies and the links between them
- `Dependency` can be either:
  - an interface (class or function)
  - or a structured dependency linking an implementation to an interface
- `Context`: contexts in which dependencies will live:
  - `APPLICATION`: equivalent to singletons across the app lifetime -- must be thread and async safe
  - `THREAD`: singleton per thread -- must be async safe
  - `TASK`: one instance will be provided for the entire task -- could be async safe
  - `FACTORY`: one instance will be provided every time it is requested
- `ContextualizedDependency`: enriched dependency with context related attributes
- `ContextualizedContainer`: one per context, handles their dependencies lifecycle
- `Provider`: wraps injection for different interfaces (classes, functions, methods)
- `Package`: provides for more dependency declaration and add grouped dependencies to the container


## Usage

### Summary

The container should be initialized somewhere near the entrypoint of the application.
```python
from imbue import Container, Context, ContextualizedDependency

from myapp import APkg, ADep, BDep

container = Container(
    APkg(...),  # Packages would typically be passed config.
    ContextualizedDependency(ADep, Context.THREAD, eager=True),
)

...

# The application context should be entered through the framework initialization.
async with container.application_context() as app_container:
    a_dep = await app_container.get(ADep)
    ...
    # The task context should be entered in each request.
    async with app_container.task_context() as task_container:
        b_dep = await task_container.get(BDep)
```

> [!TIP]
> A dependency can require other dependencies, the container will resolve the graph and raise errors if circular dependencies are found.

> [!NOTE]
> For non async code, use `container.sync_application_context`.

### In the details
The packages provide the dependencies for the container, there are two ways of doing that.

#### Complex dependencies
This might be because dependencies depend on config and other reasons.
You can use the `Package` class:
```python
from typing import AsyncIterator

from imbue import Package, application_context

from myapp import LoggingConfig, MyLoggerTransport, LoggerTransport, MyLogger, Logger

class LoggingPackage(Package):
    def __init__(self, config: LoggingConfig):
        self._config = config
        
    @application_context(eager=True)  # You can autoload dependencies.
    # The method should expose the interface as the type and return the implementation.
    def logger_transport(self) -> LoggerTransport:
        return MyLoggerTransport(self._config.transport)

    @application_context
    # Sub dependencies should be required through their interface.
    async def logger(self, transport: LoggerTransport) -> AsyncIterator[Logger]:
        # Package methods also allow you to handle context managers.
        async with MyLogger(transport, self._config.logger) as logger:
            # Using generators allow cleaning up resources when the context closes.
            yield logger
```

##### Declaring dependencies
It's done via methods that can be:
- functions
- async functions
- generators
- async generators

To declare the method returns a dependency, you simply choose the appropriate context and add the context decorator on the method.

> [!TIP]
> Eager dependencies are instantiated as soon as we enter their context.
> This is useful if we want to make sure a dependency will use the main thread's event loop.

##### Cleaning resources
When you need to close resources you can do so via a generator.
The generator should yield the dependency.

> [!WARNING]
> You should watch out for errors, if the context is closed handling an error, it will be raised in the generator.

#### Simple dependencies
You can directly pass them to the container:
```python
Container(
    # Directly expose the implementation.
    ARepo,
    # Or interfaced implementations.
    Interfaced(BRepoInterface, BRepoImplementation),
    # You can also this to control context and eagerness.
    ContextualizedDependency(CDep, Context.THREAD, eager=True),
    ...,
)
```
or if you want to include them in a `Package`, add them in `EXTRA_DEPENDENCIES`.

> [!NOTE]
> Whatever the method of adding dependencies,
> non-contextualized ones will have the context automatically set based on sub-dependencies.
> The lowest possible context will be used.

## Integrations

- [FastAPI](./imbue/fastapi/README.md)
