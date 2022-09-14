import json
import os.path
import re
from dataclasses import dataclass
from os import listdir
from re import Pattern
from sys import argv
from typing import List, Optional, Union, Dict, Any

SerialNumber = List[int]


def to_int(serial_number: SerialNumber) -> int:
    return int(''.join(map(str, serial_number)))


@dataclass
class Product:
    name: str


@dataclass
class Courier:
    code: str
    name: str


class SerialNumberParser:
    def parse(self, number: str) -> SerialNumber:
        raise NotImplementedError


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


class DefaultSerialNumberParser(SerialNumberParser):
    def __init__(self, prepend_if: Optional[PrependIf] = None):
        self.prepend_if = prepend_if

    def parse(self, number: str) -> SerialNumber:
        if self.prepend_if:
            number = self.prepend_if.apply(number)

        return [int(digit) for digit in number]

    @classmethod
    def from_spec(cls, validation_spec: Dict[str, Any]) -> 'SerialNumberParser':
        serial_number_format = validation_spec.get('serial_number_format')
        if not serial_number_format:
            return DefaultSerialNumberParser()

        prepend_if_spec = serial_number_format.get('prepend_if')
        if not prepend_if_spec:
            return DefaultSerialNumberParser()

        prepend_if = PrependIf(
            matches_regex=_pcre_to_python_re(prepend_if_spec['matches_regex']),
            content=prepend_if_spec['content'],
        )

        return DefaultSerialNumberParser(prepend_if)


class UPSSerialNumberParser(SerialNumberParser):
    def parse(self, number: str) -> SerialNumber:
        return [self._value_of(ch) for ch in number]

    @staticmethod
    def _value_of(ch: str) -> int:
        # Can't find a definitive spec for _why_ the chars are mapped this way
        # but I did manage to find the following articles that help to confirm
        # https://abelable.altervista.org/check-digit-function-for-an-ups-tracking-number/
        # https://www.codeproject.com/articles/21224/calculating-the-ups-tracking-number-check-digit
        return int(ch) if ch.isdigit() else (ord(ch) - 3) % 10


@dataclass
class TrackingNumber:
    courier: Courier
    product: Product
    tracking_url: Optional[str]
    serial_number: SerialNumber
    is_valid: bool


class ChecksumValidator:
    def passes(self, serial_number: SerialNumber, check_digit: int) -> bool:
        raise NotImplementedError

    @classmethod
    def from_spec(cls, validation_spec: Dict[str, Any]) -> 'ChecksumValidator':
        checksum_spec = validation_spec.get('checksum')
        if not checksum_spec:
            return NoChecksum()

        strategy = checksum_spec.get('name')
        if strategy == 's10':
            return S10()
        elif strategy == 'mod7':
            return Mod7()
        elif strategy == 'mod10':
            return Mod10(
                odds_multiplier=checksum_spec.get('odds_multiplier'),
                evens_multiplier=checksum_spec.get('evens_multiplier'),
            )
        elif strategy == 'sum_product_with_weightings_and_modulo':
            return SumProductWithWeightsAndModulo(
                weights=checksum_spec['weightings'],
                first_modulo=checksum_spec['modulo1'],
                second_modulo=checksum_spec['modulo2'],
            )

        raise ValueError(f'Unknown checksum: {strategy}')


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


class TrackingNumberDefinition:
    courier: Courier
    product: Product
    number_regex: Pattern
    tracking_url_template: Optional[str]
    serial_number_parser: SerialNumberParser
    checksum_validator: ChecksumValidator

    def __init__(
        self,
        courier: Courier,
        product: Product,
        number_regex: Pattern,
        tracking_url_template: Optional[str],
        serial_number_parser: SerialNumberParser,
        checksum_validator: ChecksumValidator,
    ):
        self.courier = courier
        self.product = product
        self.number_regex = number_regex
        self.tracking_url_template = tracking_url_template
        self.serial_number_parser = serial_number_parser
        self.checksum_validator = checksum_validator

    def test(self, tracking_number: str) -> Optional[TrackingNumber]:
        match = self.number_regex.match(tracking_number)
        if not match:
            return None

        match_data = match.groupdict() if match else {}
        serial_number = self.serial_number_parser.parse(
            match_data['SerialNumber'],
        )

        passes_validation = self.checksum_validator.passes(
            serial_number=serial_number,
            check_digit=int(match_data['CheckDigit']),
        )

        return TrackingNumber(
            courier=self.courier,
            product=self.product,
            tracking_url=self.tracking_url(tracking_number),
            serial_number=serial_number,
            is_valid=passes_validation,
        )

    def tracking_url(self, tracking_number: str) -> Optional[str]:
        if not self.tracking_url_template:
            return None

        return self.tracking_url_template % tracking_number


def _pcre_to_python_re(regex: str) -> Pattern:
    return re.compile(regex.replace('(?<', '(?P<'))


def _parse_regex(raw_regex: Union[str, List[str]]) -> Pattern:
    if isinstance(raw_regex, list):
        raw_regex = ''.join(raw_regex)

    return _pcre_to_python_re(raw_regex)


def _parse_definitions(data: Dict[str, Any]) -> List[TrackingNumberDefinition]:
    definitions: List[TrackingNumberDefinition] = []
    for tn_data in data['tracking_numbers']:
        tracking_url_template = tn_data.get('tracking_url')
        number_regex = _parse_regex(tn_data['regex'])

        validation_spec = tn_data['validation']
        serial_number_parser = (
            UPSSerialNumberParser()
            if data['courier_code'] == 'ups'
            else DefaultSerialNumberParser.from_spec(validation_spec)
        )

        definitions.append(
            TrackingNumberDefinition(
                number_regex=number_regex,
                tracking_url_template=tracking_url_template,
                checksum_validator=ChecksumValidator.from_spec(validation_spec),
                serial_number_parser=serial_number_parser,
                product=Product(name=tn_data['name']),
                courier=Courier(
                    name=data['name'],
                    code=data['courier_code'],
                ),
            )
        )

    return definitions


def load_definitions(base_dir: str) -> List[TrackingNumberDefinition]:
    definitions: List[TrackingNumberDefinition] = []
    for filename in listdir(base_dir):
        path = os.path.join(base_dir, filename)
        with open(path) as f:
            data = json.load(f)
            definitions_from_file = _parse_definitions(data)
            definitions.extend(definitions_from_file)

    return definitions


def main():
    raw_tracking_number = argv[1]
    definitions = load_definitions('tracking_number_data/couriers')
    for definition in definitions:
        tracking_number = definition.test(raw_tracking_number)
        if tracking_number:
            print(tracking_number)
            # print(definition.serial_number_parser.parse(tracking_number))
            # print(definition.tracking_url(tracking_number))


if __name__ == '__main__':
    main()
