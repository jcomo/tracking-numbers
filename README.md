<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [tracking-numbers](#tracking-numbers)
  - [Why?](#why)
  - [Installation](#installation)
  - [Usage](#usage)
    - [`get_tracking_number(number)`](#get_tracking_numbernumber)
    - [`get_definition(product_name)`](#get_definitionproduct_name)
  - [Testing](#testing)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# tracking-numbers

A library that parses tracking numbers and provides common types.
The data is sourced from [`tracking_number_data`](https://github.com/jkeen/tracking_number_data/) and the definitions are code-generated.

## Why?

The typical shipping tracking number has a lot of data encoded within.
While some couriers share similar logic (serial number, check digit, etc), others have entirely different ways of representing tracking numbers.

Instead of hand-rolling parsing code for all of these cases, the author of [`tracking_number_data`](https://github.com/jkeen/tracking_number_data/) has put together a repo that serves as a language-agnostic source of knowledge for various couriers and their shipping products.

This library uses that data to code-generate definitions to create python bindings for parsing tracking numbers.

The library itself has no external dependencies, and can be used to decode basic tracking data without the need of an API or external data source at runtime.

## Installation

Install the tracking-numbers library using pypi

```sh
pip install tracking-numbers
```

## Usage

Here are the main public functions to use:

### `get_tracking_number(number)`

Parses the `number` and returns the `TrackingNumber` dataclass, if detected, or none otherwise.

```python
from tracking_numbers import get_tracking_number

tracking_number = get_tracking_number("1ZY0X1930320121606")

# => TrackingNumber(
#       valid=False,
#       number='1ZY0X1930320121606',
#       serial_number=[6, 0, 5, 1, 9, 3, 0, 3, 2, 0, 1, 2, 1, 6, 0],
#       tracking_url='https://wwwapps.ups.com/WebTracking/track?track=yes&trackNums=1ZY0X1930320121604',
#       courier=Courier(code='ups', name='UPS'),
#       product=Product(name='UPS'),
#    )
```

### `get_tracking_numbers(number)`

Parses the `number` and returns all possible corresponding `TrackingNumber` dataclasses

```python
from tracking_numbers import get_tracking_numbers

tracking_numbers = get_tracking_numbers("93001109246000000072710271")

# => [
#        TrackingNumber(
#            valid=True,
#            number="93001109246000000072710271",
#            serial_number=[9, 3, 0, 0, 1, 1, 0, 9, 2, 4],
#            tracking_url="http://www.dhl.com/en/express/tracking.html?brand=DHL&AWB=93001109246000000072710271",
#            courier=Courier(code="dhl", name="DHL"),
#            product=Product(name="DHL Express Air"),
#        ),
#        TrackingNumber(
#            valid=True,
#            number="93001109246000000072710271",
#            serial_number=[9, 3, 0, 0, 1, 1, 0, 9, 2, 4, 6, 0, 0, 0, 0, 0, 0, 0, 7, 2, 7, 1, 0, 2, 7],
#            tracking_url="https://tools.usps.com/go/TrackConfirmAction?tLabels=93001109246000000072710271",
#            courier=Courier(code="usps", name="United States Postal Service"),
#            product=Product(name="USPS 91"),
#        )
# ]
```

### `get_definition(product_name)`

Given a product name, gets the `TrackingNumberDefinition` associated.
You can call `definition.test(number)` to parse a number for that specific product.

```python
from tracking_numbers import get_definition

ups_definition = get_definition('UPS')
tracking_number = ups_definition.test("1ZY0X1930320121606")

# => TrackingNumber(
#       valid=False,
#       number='1ZY0X1930320121606',
#       serial_number=[6, 0, 5, 1, 9, 3, 0, 3, 2, 0, 1, 2, 1, 6, 0],
#       tracking_url='https://wwwapps.ups.com/WebTracking/track?track=yes&trackNums=1ZY0X1930320121604',
#       courier=Courier(code='ups', name='UPS'),
#       product=Product(name='UPS'),
#    )

tracking_number = ups_definition.test('some_valid_fedex_number')

# => None
```

## Testing

We use the test cases defined in the courier data to generate pytest test cases.
In this way, we can be confident that the logic for parsing tracking numbers is working properly.
