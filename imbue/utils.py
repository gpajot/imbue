import functools
import inspect
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Set,
    get_type_hints,
)

from imbue.exceptions import DependencyError


@dataclass
class Annotation:
    annotation: Any
    mandatory: bool


def get_annotations(
    func: Callable,
    with_return: bool = True,
    with_instance: bool = True,
) -> Dict[str, Annotation]:
    """Wrapper around signature and get_type_hints functions.
    Note: variadic and positional only parameters are excluded as those make injection risky.
    """
    hints = get_type_hints(func)
    signature = inspect.signature(func)
    annotations = {
        # Use annotations or default to signature annotation.
        # We still have to use the annotations since they are resolved if needed ("Cls" -> Cls).
        p.name: Annotation(
            hints[p.name] if p.name in hints else p.annotation,
            mandatory=p.default is p.empty,
        )
        for p in signature.parameters.values()
        if p.kind
        not in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
            inspect.Parameter.VAR_POSITIONAL,
        )
        and (with_instance or p.name not in ("self", "cls"))
    }
    if with_return:
        annotations["return"] = Annotation(
            hints["return"] if "return" in hints else signature.return_annotation,
            mandatory=False,
        )
    return annotations


def partial(func: Callable, **kwargs: Any) -> Callable:
    """Replacement of `functools.partial` to make it work with type hints.
    Note: this is just smoke to allow programmatically parsing the signature.
    """
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def _wrapper(*a, **kw):
            return await func(*a, **kwargs, **kw)

    else:

        @functools.wraps(func)
        def _wrapper(*a, **kw):
            return func(*a, **kwargs, **kw)

    # Update the annotations and signature of the function to remove injected arguments.
    _wrapper.__annotations__ = {
        k: v.annotation for k, v in get_annotations(func).items() if k not in kwargs
    }
    signature = inspect.signature(func)
    _wrapper.__signature__ = signature.replace(  # type: ignore[attr-defined]
        parameters=[p for p in signature.parameters.values() if p.name not in kwargs],
    )
    return _wrapper


def extend(
    func: Callable,
    remove_instance: bool = False,
    remove: Optional[Set[str]] = None,
) -> Callable:
    """Decorator to extend function in order to add parameters and fix signature.
    Note: this is just smoke to allow programmatically parsing the signature.
    Parameters should be added first, and have a name with no risk to collide with existing parameters.
    """
    remove_params: Set[str] = remove or set()
    if remove_instance:
        remove_params.add("self")

    def _wrapper(wrapped: Callable) -> Callable:
        wrapped_hints = get_annotations(wrapped, with_return=False)
        _wrapped = functools.wraps(func)(wrapped)

        # Handle annotations.
        # Shallow copy to avoid altering original function.
        _wrapped.__annotations__ = dict(_wrapped.__annotations__)
        for name, ann in wrapped_hints.items():
            if name in _wrapped.__annotations__:
                raise DependencyError(
                    f"parameter {name} already declared in function {func!r}",
                )
            _wrapped.__annotations__[name] = ann.annotation
        for name in remove_params:
            _wrapped.__annotations__.pop(name, None)

        signature = inspect.signature(func)
        _wrapped.__signature__ = signature.replace(  # type: ignore[attr-defined]
            parameters=[
                inspect.Parameter(
                    n,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=a.annotation,
                )
                for n, a in wrapped_hints.items()
            ]
            + [p for p in signature.parameters.values() if p.name not in remove_params],
        )
        return _wrapped

    return _wrapper
