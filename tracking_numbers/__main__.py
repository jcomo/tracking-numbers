from sys import argv

from tracking_numbers import get_tracking_number


def main():
    tracking_number = get_tracking_number(argv[1])
    if tracking_number:
        print(tracking_number)


if __name__ == "__main__":
    main()
