from typing import Optional
from typing import Pattern

from tracking_numbers.checksum_validator import ChecksumValidator
from tracking_numbers.compat import parse_regex
from tracking_numbers.serial_number import DefaultSerialNumberParser
from tracking_numbers.serial_number import SerialNumberParser
from tracking_numbers.serial_number import UPSSerialNumberParser
from tracking_numbers.types import Courier
from tracking_numbers.types import Product
from tracking_numbers.types import Spec
from tracking_numbers.types import TrackingNumber


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

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"courier={self.courier}, "
            f"product={self.product}, "
            f"number_regex=re.compile({repr(self.number_regex.pattern)}), "
            f"tracking_url_template={repr(self.tracking_url_template)}, "
            f"serial_number_parser={repr(self.serial_number_parser)}, "
            f"checksum_validator={repr(self.checksum_validator)}"
            f")"
        )

    @classmethod
    def from_spec(cls, courier: Courier, tn_spec: Spec) -> "TrackingNumberDefinition":
        tracking_url_template = tn_spec.get("tracking_url")
        number_regex = parse_regex(tn_spec["regex"])

        validation_spec = tn_spec["validation"]
        serial_number_parser = (
            UPSSerialNumberParser()
            if courier.code == "ups"
            else DefaultSerialNumberParser.from_spec(validation_spec)
        )

        return TrackingNumberDefinition(
            number_regex=number_regex,
            tracking_url_template=tracking_url_template,
            checksum_validator=ChecksumValidator.from_spec(validation_spec),
            serial_number_parser=serial_number_parser,
            product=Product(name=tn_spec["name"]),
            courier=courier,
        )

    def test(self, tracking_number: str) -> Optional[TrackingNumber]:
        match = self.number_regex.match(tracking_number)
        if not match:
            return None

        match_data = match.groupdict() if match else {}
        serial_number = self.serial_number_parser.parse(
            "".join(ch for ch in match_data["SerialNumber"] if ch.strip()),
        )

        passes_validation = self.checksum_validator.passes(
            serial_number=serial_number,
            check_digit=int(match_data.get("CheckDigit", 0)),
        )

        return TrackingNumber(
            valid=passes_validation,
            number=tracking_number,
            serial_number=serial_number,
            tracking_url=self.tracking_url(tracking_number),
            courier=self.courier,
            product=self.product,
        )

    def tracking_url(self, tracking_number: str) -> Optional[str]:
        if not self.tracking_url_template:
            return None

        return self.tracking_url_template % tracking_number
