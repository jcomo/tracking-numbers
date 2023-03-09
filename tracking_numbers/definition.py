from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Optional
from typing import Pattern

from tracking_numbers.checksum_validator import ChecksumValidator
from tracking_numbers.compat import parse_regex
from tracking_numbers.helpers.repr import repr_with_args
from tracking_numbers.serial_number import DefaultSerialNumberParser
from tracking_numbers.serial_number import SerialNumberParser
from tracking_numbers.serial_number import UPSSerialNumberParser
from tracking_numbers.types import Courier
from tracking_numbers.types import Product
from tracking_numbers.types import SerialNumber
from tracking_numbers.types import Spec
from tracking_numbers.types import TrackingNumber
from tracking_numbers.types import ValidationError
from tracking_numbers.value_matcher import ValueMatcher

MatchData = Dict[str, str]


@dataclass
class AdditionalValidation:
    name: str
    regex_group_name: str
    value_matchers: List[ValueMatcher]

    @classmethod
    def from_spec(cls, spec: Spec) -> "AdditionalValidation":
        value_matchers: List[ValueMatcher] = []
        for value_matcher_spec in spec["lookup"]:
            value_matchers.append(ValueMatcher.from_spec(value_matcher_spec))

        return AdditionalValidation(
            name=spec["name"],
            regex_group_name=spec["regex_group_name"],
            value_matchers=value_matchers,
        )


class TrackingNumberDefinition:
    courier: Courier
    product: Product
    number_regex: Pattern
    tracking_url_template: Optional[str]
    serial_number_parser: SerialNumberParser
    checksum_validator: Optional[ChecksumValidator]
    additional_validations: List[AdditionalValidation]

    def __init__(
        self,
        courier: Courier,
        product: Product,
        number_regex: Pattern,
        tracking_url_template: Optional[str],
        serial_number_parser: SerialNumberParser,
        checksum_validator: Optional[ChecksumValidator],
        additional_validations: List[AdditionalValidation],
    ):
        self.courier = courier
        self.product = product
        self.number_regex = number_regex
        self.tracking_url_template = tracking_url_template
        self.serial_number_parser = serial_number_parser
        self.checksum_validator = checksum_validator
        self.additional_validations = additional_validations

    def __repr__(self):
        return repr_with_args(
            self,
            courier=self.courier,
            product=self.product,
            number_regex=self.number_regex,
            tracking_url_template=self.tracking_url_template,
            serial_number_parser=self.serial_number_parser,
            checksum_validator=self.checksum_validator,
            additional_validations=self.additional_validations,
        )

    @classmethod
    def from_spec(cls, courier: Courier, tn_spec: Spec) -> "TrackingNumberDefinition":
        product = Product(name=tn_spec["name"])
        tracking_url_template = tn_spec.get("tracking_url")
        number_regex = parse_regex(tn_spec["regex"])

        validation_spec = tn_spec["validation"]
        serial_number_parser = (
            UPSSerialNumberParser()
            if courier.code == "ups"
            else DefaultSerialNumberParser.from_spec(validation_spec)
        )

        additional_spec = tn_spec.get("additional")
        additional_validations: List[AdditionalValidation] = []
        if isinstance(additional_spec, list):
            # Handles None and 1 that is a dict (seems like old format / mistake)
            for spec in additional_spec:
                additional_validations.append(AdditionalValidation.from_spec(spec))

        return TrackingNumberDefinition(
            courier=courier,
            product=product,
            number_regex=number_regex,
            tracking_url_template=tracking_url_template,
            serial_number_parser=serial_number_parser,
            checksum_validator=ChecksumValidator.from_spec(validation_spec),
            additional_validations=additional_validations,
        )

    def test(self, tracking_number: str) -> Optional[TrackingNumber]:
        match = self.number_regex.fullmatch(tracking_number)
        if not match:
            return None

        match_data = match.groupdict() if match else {}
        serial_number = self._get_serial_number(match_data)
        validation_errors = self._get_validation_errors(serial_number, match_data)

        return TrackingNumber(
            number=tracking_number,
            courier=self.courier,
            product=self.product,
            serial_number=serial_number,
            tracking_url=self.tracking_url(tracking_number),
            validation_errors=validation_errors,
        )

    def _get_serial_number(self, match_data: MatchData) -> Optional[SerialNumber]:
        raw_serial_number = match_data.get("SerialNumber")
        if raw_serial_number:
            return self.serial_number_parser.parse(
                _remove_whitespace(raw_serial_number),
            )

        return None

    def _get_validation_errors(
        self,
        serial_number: Optional[SerialNumber],
        match_data: MatchData,
    ) -> List[ValidationError]:
        errors: List[ValidationError] = []
        checksum_error = self._get_checksum_errors(serial_number, match_data)
        if checksum_error:
            errors.append(checksum_error)

        for validation in self.additional_validations:
            additional_error = self._get_additional_error(validation, match_data)
            if additional_error:
                errors.append(additional_error)

        return errors

    def _get_checksum_errors(
        self,
        serial_number: Optional[SerialNumber],
        match_data: MatchData,
    ) -> Optional[ValidationError]:
        if not self.checksum_validator:
            return None

        if not serial_number:
            return "checksum", "SerialNumber not found"

        check_digit = match_data.get("CheckDigit")
        if not check_digit:
            return "checksum", "CheckDigit not found"

        passes_checksum = self.checksum_validator.passes(
            serial_number=serial_number,
            check_digit=int(check_digit),
        )

        if not passes_checksum:
            return "checksum", "Checksum validation failed"

        return None

    @staticmethod
    def _get_additional_error(
        validation: AdditionalValidation,
        match_data: MatchData,
    ) -> Optional[ValidationError]:
        group_key = validation.regex_group_name
        raw_value = match_data.get(group_key)
        if not raw_value:
            return validation.name, f"{group_key} not found"

        value = _remove_whitespace(raw_value)
        matches_any_value = any(
            value_matcher.matches(value) for value_matcher in validation.value_matchers
        )

        if not matches_any_value:
            return validation.name, f"Match not found for {group_key}: {value}"

        return None

    def tracking_url(self, tracking_number: str) -> Optional[str]:
        if not self.tracking_url_template:
            return None

        return self.tracking_url_template % tracking_number


def _remove_whitespace(value: str) -> str:
    return "".join(ch for ch in value if ch.strip())
