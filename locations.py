import random

_locations_filename = 'locations.txt'
locations = []


def add_location(location: str):
    if location not in locations:
        locations.append(location)
        with open(_locations_filename, 'a') as f:
            print(location, file=f)


def read_locations() -> list[str]:
    with open(_locations_filename) as f:
        locations = f.read().splitlines()
        return locations


def update_location_list(new_locations: list):
    locations = new_locations
    with open(_locations_filename, 'w') as f:
        print('\n'.join(new_locations), file=f)


def choose_location() -> str:
    return random.choice(locations)


locations = read_locations()
