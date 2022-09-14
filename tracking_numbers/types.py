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
    courier: Courier
    product: Product
    tracking_url: Optional[str]
    serial_number: SerialNumber
    is_valid: bool


def to_int(serial_number: SerialNumber) -> int:
    return int("".join(map(str, serial_number)))
