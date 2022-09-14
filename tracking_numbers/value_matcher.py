import re
from abc import ABCMeta
from abc import abstractmethod
from re import Pattern

from tracking_numbers.types import Spec


class ValueMatcher(metaclass=ABCMeta):
    @abstractmethod
    def __repr__(self):
        raise NotImplementedError

    @abstractmethod
    def matches(self, other: str) -> bool:
        raise NotImplementedError

    @classmethod
    def from_spec(cls, spec: Spec) -> "ValueMatcher":
        if "matches" in spec:
            return ExactValueMatcher(spec["matches"])
        elif "matches_regex" in spec:
            return RegexValueMatcher(spec["matches_regex"])

        raise ValueError(f"Invalid matcher spec: {spec}")


class ExactValueMatcher(ValueMatcher):
    def __init__(self, value: str):
        self.value = value

    def __repr__(self):
        return f"{self.__class__.__name__}(value={repr(self.value)})"

    def matches(self, other: str) -> bool:
        return self.value == other


class RegexValueMatcher(ValueMatcher):
    def __init__(self, pattern: Pattern):
        self.pattern = re.compile(pattern)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"pattern=re.compile({repr(self.pattern.pattern)})"
            f")"
        )

    def matches(self, other: str) -> bool:
        return bool(self.pattern.match(other))
