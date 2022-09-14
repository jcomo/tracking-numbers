from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

Spec = Dict[str, Any]
SerialNumber = List[int]


@dataclass
class Product:
    name: str


@dataclass
class Courier:
    code: str
    name: str


@dataclass
class TrackingNumber:
    valid: bool
    number: str
    serial_number: SerialNumber
    tracking_url: Optional[str]
    courier: Courier
    product: Product


def to_int(serial_number: SerialNumber) -> int:
    return int("".join(map(str, serial_number)))
