import json
import pickle

from .models import Slot

LEGACY_WIDTH = 107
LEGACY_HEIGHT = 48


def load_legacy_positions(path):
    """Read legacy slot top-left corners from the pickle file or a JSON list."""
    with open(path, "rb") as file:
        if str(path).endswith(".json"):
            data = json.load(file)
        else:
            data = pickle.load(file)

    positions = []
    for entry in data:
        if isinstance(entry, dict):
            entry = (entry["x"], entry["y"])
        positions.append((int(entry[0]), int(entry[1])))
    return positions


def corners_from_top_left(x, y, width=LEGACY_WIDTH, height=LEGACY_HEIGHT):
    return [[x, y], [x + width, y], [x + width, y + height], [x, y + height]]


def slot_entries(positions, width=LEGACY_WIDTH, height=LEGACY_HEIGHT):
    return [
        {"name": f"S{i}", "coordinates": corners_from_top_left(x, y, width, height)}
        for i, (x, y) in enumerate(positions, start=1)
    ]


def import_legacy_slots(path, width=LEGACY_WIDTH, height=LEGACY_HEIGHT):
    """Insert legacy positions into the slots table; returns how many were created."""
    created = 0
    for entry in slot_entries(load_legacy_positions(path), width, height):
        _, was_created = Slot.objects.get_or_create(
            name=entry["name"], defaults={"coordinates": entry["coordinates"]}
        )
        created += was_created
    return created
