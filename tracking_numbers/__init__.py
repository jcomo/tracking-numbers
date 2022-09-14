__version__ = "0.1.0"

from typing import List, Optional

from tracking_numbers.definition import TrackingNumberDefinition
from tracking_numbers.types import TrackingNumber
from tracking_numbers.utils import iter_courier_specs, iter_definitions


def _load_all_definitions():
    all_definitions: List[TrackingNumberDefinition] = []
    for courier_spec in iter_courier_specs():
        for tn_definition, _ in iter_definitions(courier_spec):
            all_definitions.append(tn_definition)

    return all_definitions


_ALL_DEFINITIONS = _load_all_definitions()


def get_tracking_number(number: str) -> Optional[TrackingNumber]:
    for tn_definition in _ALL_DEFINITIONS:
        tracking_number = tn_definition.test(number)
        if tracking_number:
            return tracking_number

    return None
