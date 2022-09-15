from re import Pattern
from typing import Any


def repr_with_args(self: Any, *args, **kwargs):
    args_repr = [_smart_repr(arg) for arg in args]
    kwargs_repr = [f"{key}={_smart_repr(value)}" for key, value in kwargs.items()]
    args_and_kwargs = ", ".join(args_repr + kwargs_repr)
    return f"{self.__class__.__name__}({args_and_kwargs})"


def _smart_repr(value: Any) -> str:
    if isinstance(value, Pattern):
        # Since we're using this for codegen, we need to use our own implementation
        # of repr(...) since python truncates the pattern in its default impl
        # See: https://stackoverflow.com/a/30222089
        return f"re.compile({repr(value.pattern)})"

    return repr(value)
