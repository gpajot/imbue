import inspect
from typing import get_type_hints

import pytest

from imbue.exceptions import DependencyError
from imbue.utils import Annotation, extend, get_annotations, partial


@pytest.fixture()
def func():
    def f(a: int, b: str) -> str:
        return f"{a}-{b}"

    return f


@pytest.fixture()
def async_func():
    async def f(a: int, b: str) -> str:
        return f"{a}-{b}"

    return f


@pytest.fixture()
def variadic_func():
    def f(*args, **kwargs) -> str:
        return ""

    return f


class A:
    def f(self: "A", a: int, b: str) -> str:
        return f"{a}-{b}"


def test_partial_get_type_hints(func):
    assert get_type_hints(partial(func, a=1)) == {"b": str, "return": str}
    assert get_type_hints(partial(func, b="1")) == {"a": int, "return": str}
    assert get_type_hints(partial(func, a=1, b="1")) == {"return": str}


def test_partial_signature(func):
    assert list(inspect.signature(partial(func, a=1)).parameters) == ["b"]
    assert list(inspect.signature(partial(func, b="1")).parameters) == ["a"]
    assert list(inspect.signature(partial(func, a=1, b="1")).parameters) == []


def test_partial_call(func):
    assert partial(func, a=1)(b="1") == "1-1"
    assert partial(func, b="1")(1) == "1-1"
    assert partial(func, a=1, b="1")() == "1-1"


def test_partial_async_get_type_hints(async_func):
    assert get_type_hints(partial(async_func, a=1)) == {"b": str, "return": str}
    assert get_type_hints(partial(async_func, b="1")) == {"a": int, "return": str}
    assert get_type_hints(partial(async_func, a=1, b="1")) == {"return": str}


def test_partial_async_signature(async_func):
    assert list(inspect.signature(partial(async_func, a=1)).parameters) == ["b"]
    assert list(inspect.signature(partial(async_func, b="1")).parameters) == ["a"]
    assert list(inspect.signature(partial(async_func, a=1, b="1")).parameters) == []


async def test_partial_async_call(async_func):
    assert await partial(async_func, a=1)(b="1") == "1-1"
    assert await partial(async_func, b="1")(1) == "1-1"
    assert await partial(async_func, a=1, b="1")() == "1-1"


def test_get_annotations(func):
    assert get_annotations(func) == {
        "a": Annotation(int, True),
        "b": Annotation(str, True),
        "return": Annotation(str, False),
    }


def test_get_annotations_without_return(func):
    assert get_annotations(func, with_return=False) == {
        "a": Annotation(int, True),
        "b": Annotation(str, True),
    }


def test_get_annotations_variadic(variadic_func):
    assert get_annotations(variadic_func) == {"return": Annotation(str, False)}


def test_get_annotations_class_method():
    assert get_annotations(A.f) == {
        "self": Annotation(A, True),
        "a": Annotation(int, True),
        "b": Annotation(str, True),
        "return": Annotation(str, False),
    }
    assert get_annotations(A.f, with_instance=False) == {
        "a": Annotation(int, True),
        "b": Annotation(str, True),
        "return": Annotation(str, False),
    }


def test_extend_remove_instance():
    @extend(A.f, remove_instance=True)
    def wrapped(*args, **kwargs):
        pass

    assert get_type_hints(wrapped) == {"a": int, "b": str, "return": str}
    assert list(inspect.signature(wrapped).parameters) == ["a", "b"]


def test_extend_remove_parameters():
    @extend(A.f, remove={"a"})
    def wrapped(*args, **kwargs):
        pass

    assert get_type_hints(wrapped) == {"self": A, "b": str, "return": str}
    assert list(inspect.signature(wrapped).parameters) == ["self", "b"]


def test_extend_add_parameters(func):
    @extend(func)
    def wrapped(_c: str, _d: str, *args, **kwargs):
        return f"{func(*args, **kwargs)}-{_c}-{_d}"

    assert wrapped("3", "4", 1, "2") == "1-2-3-4"
    assert get_type_hints(wrapped) == {
        "_c": str,
        "_d": str,
        "a": int,
        "b": str,
        "return": str,
    }
    assert list(inspect.signature(wrapped).parameters) == ["_c", "_d", "a", "b"]


def test_extend_add_same_parameter():
    def f(a: int):
        pass

    def wrapped(a: str, *args, **kwargs):
        pass

    with pytest.raises(DependencyError, match="already declared"):
        extend(f)(wrapped)


def test_extend_stateless(func):
    def wrapped1(_a: str, *args, **kwargs):
        pass

    def wrapped2(_a: str, *args, **kwargs):
        pass

    extend(func)(wrapped1)
    # Check we can call it multiple times.
    extend(func)(wrapped2)
    # Check original function unmodified.
    assert get_type_hints(func) == {
        "a": int,
        "b": str,
        "return": str,
    }
    assert list(inspect.signature(func).parameters) == ["a", "b"]
