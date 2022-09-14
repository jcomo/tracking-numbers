import json
import os.path
from os import listdir

from tracking_numbers.definition import TrackingNumberDefinition
from tracking_numbers.types import Courier
from tracking_numbers.types import Spec

DEFAULT_BASE_DIR = "tracking_number_data/couriers"


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
