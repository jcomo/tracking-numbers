import json
import os.path
from os import listdir
from typing import List
from typing import Tuple

from tracking_numbers.definition import TrackingNumberDefinition
from tracking_numbers.types import Courier
from tracking_numbers.types import Spec

DEFAULT_BASE_DIR = "tracking_number_data/couriers"

TestCase = Tuple[TrackingNumberDefinition, str, bool]


def iter_courier_specs(base_dir: str = DEFAULT_BASE_DIR):
    for filename in listdir(base_dir):
        path = os.path.join(base_dir, filename)
        with open(path) as f:
            yield json.load(f)


def iter_definitions(courier_spec: Spec):
    courier = Courier(
        name=courier_spec["name"],
        code=courier_spec["courier_code"],
    )

    for tn_spec in courier_spec["tracking_numbers"]:
        definition = TrackingNumberDefinition.from_spec(courier, tn_spec)
        yield definition, tn_spec


def iter_test_cases(courier_spec: Spec) -> List[TestCase]:
    test_cases: List[TestCase] = []
    for definition, tn_spec in iter_definitions(courier_spec):
        test_numbers = tn_spec.get("test_numbers")
        if not test_numbers:
            continue

        valid_numbers = test_numbers.get("valid", [])
        for valid_number in valid_numbers:
            test_cases.append((definition, valid_number, True))

        invalid_numbers = test_numbers.get("invalid", [])
        for invalid_number in invalid_numbers:
            test_cases.append((definition, invalid_number, False))

    return test_cases
