from abc import ABCMeta
from abc import abstractmethod
from typing import List
from typing import Optional

from tracking_numbers.types import SerialNumber
from tracking_numbers.types import Spec
from tracking_numbers.types import to_int


class ChecksumValidator(metaclass=ABCMeta):
    @abstractmethod
    def passes(self, serial_number: SerialNumber, check_digit: int) -> bool:
        raise NotImplementedError

    @classmethod
    def from_spec(cls, validation_spec: Spec) -> "ChecksumValidator":
        checksum_spec = validation_spec.get("checksum")
        if not checksum_spec:
            return NoChecksum()

        strategy = checksum_spec.get("name")
        if strategy == "s10":
            return S10()
        elif strategy == "mod7":
            return Mod7()
        elif strategy == "mod10":
            return Mod10(
                odds_multiplier=checksum_spec.get("odds_multiplier"),
                evens_multiplier=checksum_spec.get("evens_multiplier"),
            )
        elif strategy == "sum_product_with_weightings_and_modulo":
            return SumProductWithWeightsAndModulo(
                weights=checksum_spec["weightings"],
                first_modulo=checksum_spec["modulo1"],
                second_modulo=checksum_spec["modulo2"],
            )

        raise ValueError(f"Unknown checksum: {strategy}")


class NoChecksum(ChecksumValidator):
    def passes(self, serial_number: SerialNumber, check_digit: int) -> bool:
        return True


class S10(ChecksumValidator):
    WEIGHTS = [8, 6, 4, 2, 3, 5, 9, 7]

    def passes(self, serial_number: SerialNumber, check_digit: int) -> bool:
        total = 0
        for digit, weight in zip(serial_number, self.WEIGHTS):
            total += digit * weight

        remainder = total % 11
        if remainder == 1:
            check = 0
        elif remainder == 0:
            check = 5
        else:
            check = 11 - remainder

        return check == check_digit


class Mod10(ChecksumValidator):
    def __init__(
        self,
        odds_multiplier: Optional[int] = None,
        evens_multiplier: Optional[int] = None,
    ):
        self.odds_multiplier = odds_multiplier
        self.evens_multiplier = evens_multiplier

    def passes(self, serial_number: SerialNumber, check_digit: int) -> bool:
        total = 0
        for index, digit in enumerate(serial_number):
            is_even_index = index % 2 == 0
            is_odd_index = not is_even_index

            if is_odd_index and self.odds_multiplier:
                total += digit * self.odds_multiplier
            elif is_even_index and self.evens_multiplier:
                total += digit * self.evens_multiplier
            else:
                total += digit

        check = total % 10
        if check != 0:
            check = 10 - check

        return check == check_digit


class Mod7(ChecksumValidator):
    def passes(self, serial_number: SerialNumber, check_digit: int) -> bool:
        return check_digit == (to_int(serial_number) % 7)


class SumProductWithWeightsAndModulo(ChecksumValidator):
    def __init__(self, weights: List[int], first_modulo: int, second_modulo: int):
        self.weights = weights
        self.first_modulo = first_modulo
        self.second_modulo = second_modulo

    def passes(self, serial_number: SerialNumber, check_digit: int) -> bool:
        total = 0
        for digit, weight in zip(serial_number, self.weights):
            total += digit * weight

        check = total % self.first_modulo % self.second_modulo
        return check == check_digit
