import json
import os.path
import re
from dataclasses import dataclass
from os import listdir
from re import Pattern
from sys import argv
from typing import List, Optional, Union, Dict, Any, Tuple


@dataclass
class Product:
    name: str


@dataclass
class Courier:
    code: str
    name: str


@dataclass
class TrackingNumberDefinition:
    courier: Courier
    product: Product
    number_regex: Pattern
    tracking_url_template: Optional[str]

    def test(self, tracking_number: str) -> Tuple[bool, Dict[str, str]]:
        match = self.number_regex.match(tracking_number)
        match_data = match.groupdict() if match else {}
        return bool(match), match_data

    def tracking_url(self, tracking_number: str) -> Optional[str]:
        if not self.tracking_url_template:
            return None

        return self.tracking_url_template % tracking_number


def _parse_regex(raw_regex: Union[str, List[str]]) -> Pattern:
    if isinstance(raw_regex, list):
        raw_regex = ''.join(raw_regex)

    return re.compile(raw_regex.replace('(?<', '(?P<'))


def _parse_definitions(data: Dict[str, Any]) -> List[TrackingNumberDefinition]:
    definitions: List[TrackingNumberDefinition] = []
    for tn_data in data['tracking_numbers']:
        tracking_url_template = tn_data.get('tracking_url')
        number_regex = _parse_regex(tn_data['regex'])
        definitions.append(
            TrackingNumberDefinition(
                number_regex=number_regex,
                tracking_url_template=tracking_url_template,
                product=Product(name=tn_data['name']),
                courier=Courier(
                    name=data['name'],
                    code=data['courier_code'],
                ),
            )
        )

    return definitions


def load_definitions(base_dir: str) -> List[TrackingNumberDefinition]:
    definitions: List[TrackingNumberDefinition] = []
    for filename in listdir(base_dir):
        path = os.path.join(base_dir, filename)
        with open(path) as f:
            data = json.load(f)
            definitions_from_file = _parse_definitions(data)
            definitions.extend(definitions_from_file)

    return definitions


def main():
    tracking_number = argv[1]
    definitions = load_definitions('tracking_number_data/couriers')
    for definition in definitions:
        matches, match_data = definition.test(tracking_number)
        if matches:
            print(match_data)
            print(definition.tracking_url(tracking_number))


if __name__ == '__main__':
    main()
