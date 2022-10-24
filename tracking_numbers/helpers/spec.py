import json
import os.path
from os import listdir
from typing import List
from typing import Optional
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
            elif courier_spec["courier_code"] == "ups":
                _apply_ups_unknown_service_types_hack(courier_spec)

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
    validation_spec = _get_product_validation_spec(spec, "USPS 20", "Service Type")
    if validation_spec:
        unknown_service_type = {"matches": "03", "name": "unknown"}
        validation_spec["lookup"].insert(0, unknown_service_type)


def _apply_ups_unknown_service_types_hack(spec: Spec):
    """Adds some additional service types that are known to be valid (ie. they
    can be tracked via UPS), but are not documented in any readily available way.

    These service types may be discoverable with API access, but was not able to
    find any docs on how to do this.
    """
    additional_service_types = [
        "67",  # Found on a shipment to Canada (maybe variant of Worldwide Express?)
    ]

    validation_spec = _get_product_validation_spec(spec, "UPS", "Service Type")
    if validation_spec:
        for service_type in additional_service_types:
            service_type_spec = {"matches": service_type, "name": "unknown"}
            validation_spec["lookup"].insert(0, service_type_spec)


def _get_product_validation_spec(
    courier_spec: Spec,
    product_name: str,
    validation_name: str,
) -> Optional[Spec]:
    product_spec = _get_product_spec(courier_spec, product_name)
    if product_spec:
        validation_spec = _get_validation_spec(product_spec, validation_name)
        return validation_spec

    return None


def _get_product_spec(courier_spec: Spec, name: str) -> Optional[Spec]:
    for product_spec in courier_spec["tracking_numbers"]:
        if product_spec["name"] == name:
            return product_spec

    return None


def _get_validation_spec(product_spec: Spec, name: str) -> Optional[Spec]:
    for validation_spec in product_spec["additional"]:
        if validation_spec["name"] == name:
            return validation_spec

    return None


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
