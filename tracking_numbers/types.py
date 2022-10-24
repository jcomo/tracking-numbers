from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

Spec = Dict[str, Any]
SerialNumber = List[int]
ValidationError = Tuple[str, str]


@dataclass
class Product:
    name: str


@dataclass
class Courier:
    code: str
    name: str


@dataclass
class TrackingNumber:
    number: str
    courier: Courier
    product: Product
    serial_number: SerialNumber
    tracking_url: Optional[str]
    validation_errors: List[ValidationError]

    @property
    def valid(self) -> bool:
        return not self.validation_errors


def to_int(serial_number: SerialNumber) -> int:
    return int("".join(map(str, serial_number)))
