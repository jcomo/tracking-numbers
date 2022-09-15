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
            courier_spec = json.load(f)
            if courier_spec["courier_code"] == "usps":
                _apply_usps_20_validation_hack(courier_spec)

            yield courier_spec


def _apply_usps_20_validation_hack(spec: Spec):
    """Applies a hack to the usps courier data to include "03" as a service type.
    There are numbers marked as valid that have this service type, but it is not
    listed in the additional validation config.

    Since it is not clear if the test data is a mistake, or the validation section
    is a mistake, we apply this hack so that our test cases pass (and potentially
    cases in the wild).

    Waiting for the resolution on this Github issue:
    https://github.com/jkeen/tracking_number_data/issues/43
    """
    for product_spec in spec["tracking_numbers"]:
        if product_spec["name"] != "USPS 20":
            continue

        for validation_spec in product_spec["additional"]:
            regex_group_name = validation_spec["regex_group_name"]
            if regex_group_name == "ServiceType":
                unknown_service_type = {"matches": "03", "name": "unknown"}
                validation_spec["lookup"].insert(0, unknown_service_type)


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
