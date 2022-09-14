from examine import iter_courier_specs
from examine import iter_definitions
from examine import TrackingNumberDefinition


def id_func(val):
    """Friendlier name in test cases to easily see which case had an issue"""
    if isinstance(val, TrackingNumberDefinition):
        return val.product.name


def pytest_generate_tests(metafunc):
    test_cases = []
    for courier_spec in iter_courier_specs():
        for courier, definition, tn_spec in iter_definitions(courier_spec):
            test_numbers = tn_spec.get("test_numbers")
            if not test_numbers:
                continue

            valid_numbers = test_numbers.get("valid", [])
            for valid_number in valid_numbers:
                test_cases.append((definition, valid_number, True))

            invalid_numbers = test_numbers.get("invalid", [])
            for invalid_number in invalid_numbers:
                test_cases.append((definition, invalid_number, False))

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
