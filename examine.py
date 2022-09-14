from sys import argv

from tracking_numbers.utils import iter_courier_specs
from tracking_numbers.utils import iter_definitions


def main():
    raw_tracking_number = argv[1]
    for courier_spec in iter_courier_specs():
        for definition, _ in iter_definitions(courier_spec):
            tracking_number = definition.test(raw_tracking_number)
            if tracking_number:
                print(tracking_number)


if __name__ == "__main__":
    main()
