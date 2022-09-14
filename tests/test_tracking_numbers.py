from typing import List

from tracking_numbers import TrackingNumberDefinition
from tracking_numbers.utils import iter_courier_specs
from tracking_numbers.utils import iter_test_cases
from tracking_numbers.utils import TestCase


def id_func(val):
    """Friendlier name in test cases to easily see which case had an issue"""
    if isinstance(val, TrackingNumberDefinition):
        return val.product.name


def pytest_generate_tests(metafunc):
    test_cases: List[TestCase] = []
    for courier_spec in iter_courier_specs():
        for test_case in iter_test_cases(courier_spec):
            test_cases.append(test_case)

    metafunc.parametrize(
        argnames=["definition", "number", "expected_valid"],
        argvalues=test_cases,
        ids=id_func,
    )


def test_tracking_numbers(definition, number, expected_valid):
    tracking_number = definition.test(number)
    if not tracking_number:
        assert not expected_valid, "Expected valid tracking number, but wasn't detected"
    elif not tracking_number.is_valid:
        assert not expected_valid, "Expected valid tracking number, but was invalid"
    elif tracking_number.is_valid:
        assert expected_valid, "Expected invalid tracking number, but was valid"
