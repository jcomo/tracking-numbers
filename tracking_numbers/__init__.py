__version__ = "0.1.0"

import os
from typing import Optional

from tracking_numbers.definition import TrackingNumberDefinition
from tracking_numbers.types import TrackingNumber

if not os.environ.get("CODE_GENERATING"):
    from tracking_numbers._generated import DEFINITIONS
else:
    DEFINITIONS = []


def get_tracking_number(number: str) -> Optional[TrackingNumber]:
    for tn_definition in DEFINITIONS:
        tracking_number = tn_definition.test(number)
        if tracking_number:
            return tracking_number

    return None


def get_definition(product_name: str) -> Optional[TrackingNumberDefinition]:
    for tn_definition in DEFINITIONS:
        if tn_definition.product.name.lower() == product_name.lower():
            return tn_definition

    return None
