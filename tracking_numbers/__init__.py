__version__ = "0.1.0"

from typing import Optional

from tracking_numbers.definition import TrackingNumberDefinition
from tracking_numbers.types import TrackingNumber
from tracking_numbers.utils import iter_courier_specs, iter_definitions
from tracking_numbers._generated import DEFINITIONS


def get_tracking_number(number: str) -> Optional[TrackingNumber]:
    for tn_definition in DEFINITIONS:
        tracking_number = tn_definition.test(number)
        if tracking_number:
            return tracking_number

    return None
