import os
from typing import Optional

from tracking_numbers.definition import TrackingNumberDefinition
from tracking_numbers.types import TrackingNumber

if not os.environ.get("CODE_GENERATING"):
    from tracking_numbers._generated import DEFINITIONS
else:
    # When running codegen, it's very possible that the items in
    # DEFINITIONS are out of date / can't be successfully constructed
    # so we use an empty list so that codegen can still import utils
    DEFINITIONS = []


def get_tracking_number(number: str) -> Optional[TrackingNumber]:
    for tn_definition in DEFINITIONS:
        tracking_number = tn_definition.test(number)
        if tracking_number and tracking_number.valid:
            return tracking_number

    return None


def get_definition(product_name: str) -> Optional[TrackingNumberDefinition]:
    for tn_definition in DEFINITIONS:
        if tn_definition.product.name.lower() == product_name.lower():
            return tn_definition

    return None


def get_tracking_numbers(number: str) -> list[TrackingNumber]:
    """
    Parses the `number` and returns all possible corresponding `TrackingNumber` dataclasses
    """
    candidates = []
    for tn_definition in DEFINITIONS:
        tracking_number = tn_definition.test(number)
        if tracking_number and tracking_number.valid:
            candidates.append(tracking_number)
    return candidates
