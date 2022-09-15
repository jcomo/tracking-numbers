from dataclasses import asdict
from pprint import pprint
from sys import argv

from tracking_numbers import get_tracking_number


def main():
    tracking_number = get_tracking_number(argv[1])
    if not tracking_number:
        print("No tracking number detected!")
    else:
        pprint(asdict(tracking_number))


if __name__ == "__main__":
    main()
