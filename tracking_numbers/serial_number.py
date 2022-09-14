from abc import ABCMeta
from abc import abstractmethod
from dataclasses import dataclass
from re import Pattern
from typing import Optional

from tracking_numbers.compat import pcre_to_python_re
from tracking_numbers.types import SerialNumber
from tracking_numbers.types import Spec


@dataclass
class PrependIf:
    matches_regex: Pattern
    content: str

    def apply(self, serial_number: str) -> str:
        return (
            self.content + serial_number
            if self.matches_regex.match(serial_number)
            else serial_number
        )


class SerialNumberParser(metaclass=ABCMeta):
    @abstractmethod
    def parse(self, number: str) -> SerialNumber:
        raise NotImplementedError


class DefaultSerialNumberParser(SerialNumberParser):
    def __init__(self, prepend_if: Optional[PrependIf] = None):
        self.prepend_if = prepend_if

    def parse(self, number: str) -> SerialNumber:
        if self.prepend_if:
            number = self.prepend_if.apply(number)

        return [int(digit) for digit in number]

    @classmethod
    def from_spec(cls, validation_spec: Spec) -> "SerialNumberParser":
        serial_number_format = validation_spec.get("serial_number_format")
        if not serial_number_format:
            return DefaultSerialNumberParser()

        prepend_if_spec = serial_number_format.get("prepend_if")
        if not prepend_if_spec:
            return DefaultSerialNumberParser()

        prepend_if = PrependIf(
            matches_regex=pcre_to_python_re(prepend_if_spec["matches_regex"]),
            content=prepend_if_spec["content"],
        )

        return DefaultSerialNumberParser(prepend_if)


class UPSSerialNumberParser(SerialNumberParser):
    def parse(self, number: str) -> SerialNumber:
        return [self._value_of(ch) for ch in number]

    @staticmethod
    def _value_of(ch: str) -> int:
        # Can't find a definitive spec for _why_ the chars are mapped this way,
        # but I did manage to find the following articles that help to confirm
        # https://abelable.altervista.org/check-digit-function-for-an-ups-tracking-number/
        # https://www.codeproject.com/articles/21224/calculating-the-ups-tracking-number-check-digit
        return int(ch) if ch.isdigit() else (ord(ch) - 3) % 10
